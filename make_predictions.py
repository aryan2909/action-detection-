import cv2
import numpy as np

from training_testing import setup_model
from utils import mp_holistic, extract_keypoint_values, draw_styled_landmarks, mediapipe_detection, actions

colors = [(245, 117, 16), (117, 245, 16), (16, 117, 245)]


def prob_visualization(res, actions, input_frame, colors):
    output_frame = input_frame.copy()
    for num, prob in enumerate(res):
        cv2.rectangle(output_frame, (0, 60 + num * 40), (int(prob * 100), 90 + num * 40), colors[num], -1)
        cv2.putText(output_frame, actions[num], (0, 85 + num * 40), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2,
                    cv2.LINE_AA)

    return output_frame


sequence = []
sentence = []
predictions = []
threshold = 0.5
model = setup_model()
model.load_weights('action.h5')

cap = cv2.VideoCapture(0)
# set mediapipe model
with mp_holistic.Holistic(
        min_detection_confidence=0.5,
        min_tracking_confidence=0.5
) as holistic:
    while cap.isOpened():
        ret, frame = cap.read()

        # Make detections
        image, results = mediapipe_detection(frame, holistic)

        # Draw landmarks
        draw_styled_landmarks(image, results)

        # Prediction logic
        keypoints = extract_keypoint_values(results)

        sequence.append(keypoints)
        sequence = sequence[-30:]
        if len(sequence) == 30:
            # model handles format (num_sequences, 30, 1662)
            res = model.predict(np.expand_dims(sequence, axis=0))[0]
            image = prob_visualization(res, actions, image, colors)
            print(actions[np.argmax(res)])
            predictions.append(np.argmax(res))

            # Visualize
            if np.unique(predictions[-10:])[0] == np.argmax(res):
                if res[np.argmax(res)] > threshold:
                    if len(sentence) > 0:
                        if actions[np.argmax(res)] != sentence[-1]:
                            sentence.append(actions[np.argmax(res)])
                    else:
                        sentence.append(actions[np.argmax(res)])

            if len(sentence) > 5:
                sentence = sentence[-5:]

        cv2.rectangle(image, (0, 0), (640, 40), (245, 117, 16), -1)
        cv2.putText(image, ' '.join(sentence), (3, 30),
                    cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2, cv2.LINE_AA)

        # show frame to screen
        cv2.imshow('OpenCV Feed', image)

        # Break gracefully
        if cv2.waitKey(10) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()
