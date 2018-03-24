from math import sqrt
import numpy as np
import cv2

def parse_probabilities(filename):
    lines = []
    with open(filename, 'r') as fp:
        for line in fp:
            if line:
                lines.append(line.strip())

    return lines

if __name__ == '__main__':
    probs = parse_probabilities('probabilities')
    num_regions = len(probs) - 1  # not including original image
    num_parts = int(sqrt(num_regions))

    original_prob = float(probs[0])
    max_prob = float(max(probs))
    min_prob = float(min(probs))

    heatmap = np.zeros((32, 32, 2))
    for i in range(32):
        for j in range(32):
            heatmap[i][j] = [0, 0]

    counter = 0
    delta = [2, 2]
    part_size = [32 // 4, 32 // 4]
    divisions = [(32 - part_size[0]) // delta[0], (32 - part_size[1]) // delta[1]]
    for i in range(divisions[0] + 1):
      for j in range(divisions[1] + 1):
        x = i * delta[0]
        y = j * delta[1]
        # (x, y) is the top left corner of the rectangle

        for x_offset in range(part_size[0]):
          for y_offset in range(part_size[1]):
            heatmap[x + x_offset][y + y_offset][0] += 1
            heatmap[x + x_offset][y + y_offset][1] += float(probs[counter])

        counter += 1

    image = np.zeros((32, 32))
    # normalize
    for i in range(32):
        for j in range(32):
            if heatmap[i][j][0] == 0:
                image[i][j] = 0
            else:
                image[i][j] = heatmap[i][j][1] / heatmap[i][j][0]

    max_ = -1
    min_ = 10000000000
    for row in image:
        for elt in row:
            if elt > max_:
                max_ = elt
            if elt < min_:
                min_ = elt

    for i in range(32):
        for j in range(32):
            if max_ - min_ == 0:
                heat = 0
            else:
                heat = 1 - ((image[i][j] - min_) / (max_ - min_))

            image[i][j] = heat * 255.0

    cv2.imwrite('cat_heatmap.png', image)
