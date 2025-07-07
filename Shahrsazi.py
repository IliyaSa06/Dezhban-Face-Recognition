import cv2
import numpy as np
from skimage.metrics import structural_similarity as ssim
from matplotlib import pyplot as plt


def load_high_quality_images(image1_path, image2_path):
    """Load images while preserving maximum quality"""
    img1 = cv2.imread(image1_path, cv2.IMREAD_UNCHANGED)
    img2 = cv2.imread(image2_path, cv2.IMREAD_UNCHANGED)

    if img1 is None or img2 is None:
        raise ValueError("Error loading images")

    if img1.dtype == 'uint16':
        img1 = cv2.normalize(img1, None, 0, 255, cv2.NORM_MINMAX, cv2.CV_8U)
    if img2.dtype == 'uint16':
        img2 = cv2.normalize(img2, None, 0, 255, cv2.NORM_MINMAX, cv2.CV_8U)

    return img1, img2


def align_images(im1, im2):
    """Precise image alignment using feature matching"""
    orb = cv2.ORB_create(5000)
    kp1, des1 = orb.detectAndCompute(im1, None)
    kp2, des2 = orb.detectAndCompute(im2, None)

    bf = cv2.BFMatcher(cv2.NORM_HAMMING, crossCheck=True)
    matches = bf.match(des1, des2)
    matches = sorted(matches, key=lambda x: x.distance)

    src_pts = np.float32([kp1[m.queryIdx].pt for m in matches]).reshape(-1, 1, 2)
    dst_pts = np.float32([kp2[m.trainIdx].pt for m in matches]).reshape(-1, 1, 2)
    M, _ = cv2.findHomography(src_pts, dst_pts, cv2.RANSAC, 5.0)

    h, w = im1.shape
    aligned_img = cv2.warpPerspective(im1, M, (w, h))

    return aligned_img


def detect_changes(img1, img2, threshold=0.85, min_contour_area=100):
    """High-precision change detection"""
    score, diff = ssim(img1, img2, full=True)
    diff = (diff * 255).astype("uint8")

    _, thresh = cv2.threshold(diff, 0, 255, cv2.THRESH_BINARY_INV | cv2.THRESH_OTSU)
    contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    changed_areas = [c for c in contours if cv2.contourArea(c) > min_contour_area]

    return changed_areas, score


def save_results(img1, img2, contours, output_path='result.png'):
    """Save results with maximum quality"""
    result = img2.copy()
    cv2.drawContours(result, contours, -1, (0, 0, 255), 2)

    if output_path.endswith('.jpg') or output_path.endswith('.jpeg'):
        cv2.imwrite(output_path, result, [cv2.IMWRITE_JPEG_QUALITY, 100])
    else:
        cv2.imwrite(output_path, result, [cv2.IMWRITE_PNG_COMPRESSION, 0])


def visualize_results(img1, img2, contours):
    """Display results"""
    result = img2.copy()
    cv2.drawContours(result, contours, -1, (0, 0, 255), 2)

    plt.figure(figsize=(18, 6))

    plt.subplot(1, 3, 1)
    plt.imshow(cv2.cvtColor(img1, cv2.COLOR_BGR2RGB))
    plt.title("First Image")
    plt.axis('off')

    plt.subplot(1, 3, 2)
    plt.imshow(cv2.cvtColor(img2, cv2.COLOR_BGR2RGB))
    plt.title("Second Image")
    plt.axis('off')

    plt.subplot(1, 3, 3)
    plt.imshow(cv2.cvtColor(result, cv2.COLOR_BGR2RGB))
    plt.title("Changed Areas")
    plt.axis('off')

    plt.tight_layout()
    plt.show()


def main():
    image1_path = r"D:\Batman\Screenshot (45).png"
    image2_path = r"D:\Batman\Screenshot (44).png"
    output_path = r"D:\Batman\change_detection_result.png"

    try:
        img1, img2 = load_high_quality_images(image1_path, image2_path)
        gray1 = cv2.cvtColor(img1, cv2.COLOR_BGR2GRAY)
        gray2 = cv2.cvtColor(img2, cv2.COLOR_BGR2GRAY)

        aligned_gray1 = align_images(gray1, gray2)
        changed_areas, similarity_score = detect_changes(aligned_gray1, gray2)

        print(f"Image similarity: {similarity_score:.2%}")
        print(f"Number of changed regions: {len(changed_areas)}")

        save_results(img1, img2, changed_areas, output_path)
        visualize_results(img1, img2, changed_areas)

        print(f"Results saved to: {output_path}")

    except Exception as e:
        print(f"Error processing images: {str(e)}")


if __name__ == "__main__":
    main()