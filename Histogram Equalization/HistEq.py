import cv2
import numpy as np

#generate a historigram of the image (by manualy counting the pixels....)
def get_image_histogram(grayscale_image):
    
    #make  a list of 1x256 (one for every possible value of in the image)
    histogram = [0] * 256

    for image_height in range(grayscale_image.shape[0]):
        for image_widht in range(grayscale_image.shape[1]):
            current_pixel_value = grayscale_image[image_height][image_widht]
            
            #using the index get the value and the value as the amount
            histogram[current_pixel_value] += 1

    return histogram

#generate cumulative distribution
def get_cumulative_dist(histg):

    #running counter!
    counter = 0

    #value holder
    cuv_dist = [0] * 256

    #loop every value then add it
    for i in range(256):

        if (histg[i] > 0) :
            counter += histg[i]
            cuv_dist[i] = counter

    return cuv_dist

#returns the smallest non 0 number
def get_smallest_nz(arr):

    array_size = len(arr)
    largest = 0
    #first get the largest possible number
    for i in range(array_size):
        if (arr[i] > largest):
            largest = arr[i]

    #then try to get something smaller than that
    smallest = largest
    for i in range(array_size):
        current = arr[i]
        if(current > 0) :
            if (current < smallest) :
                #if found then set it as the value
                smallest = arr[i]

    #return the smallest value found
    return smallest


#Image Histogram equalization
def Hist_Eq(pixle_value):
    cdfv = image_cumulative_dist[pixle_value]   #get the cumulative distribution smallest value
    
    #get the image size
    x = image_gray.shape[0]
    y = image_gray.shape[1]

    upperpart = cdfv - cdfm     #caluclate the lower part of the equation 
    lowerpart = (x * y) - cdfm      #calculate the upper part of equation

    combined = float(upperpart) / float(lowerpart)  #combine both as a float falue

    result = combined * 255

    return int(result)    #return a int value


#####main code starts here!

#colored Import!
image_source =  cv2.imread('FlowerSource.jpg')

#turn into grayscale
image_gray = cv2.cvtColor(image_source, cv2.COLOR_BGR2GRAY)

#get the historgram
image_histogram = get_image_histogram(image_gray)

#get the cumulative distribution
image_cumulative_dist = get_cumulative_dist(image_histogram)

#copy the source image
hist_img = image_gray.copy()

cdfm = get_smallest_nz(image_cumulative_dist)  #get the smallest non zero value in the cumulative distribution

#loop each pixel 
for x in range(image_source.shape[0]):
    for y in range(image_source.shape[1]):
        pixel = image_gray[x][y]    #get the pixle value
        result = Hist_Eq(pixel)     #calculate the Histogram equalization
        hist_img[x][y] = result     #write the result into the duplicate image

cv2.imwrite('FlowerSource_HEQ.jpg', hist_img)
