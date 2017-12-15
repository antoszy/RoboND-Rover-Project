import numpy as np
import cv2


def color_thresh(img, rgb_above = (160, 160, 160), rgb_below = (256, 256, 256), inverse = False):
    '''Identify pixels in specified range'''
    #Create an array of zeros same xy size as img, but single channel
    color_select = np.zeros_like(img[:,:,0])
    # Require that each pixel be above all three threshold values in RGB
    # above_thresh will now contain a boolean array with "True"
    # where threshold was met
    in_range = (img[:,:,0] > rgb_above[0]) & (img[:,:,0] < rgb_below[0]) \
                 & (img[:,:,1] > rgb_above[1]) & (img[:,:,1] < rgb_below[1]) \
                 & (img[:,:,2] > rgb_above[2]) & (img[:,:,2] < rgb_below[2])


    # Index the array of zeros with the boolean array and set to 1
    if inverse: color_select[~in_range] = 1
    else: color_select[in_range] = 1


    # Return the binary image
    return color_select

# Define a function to convert from image coords to rover coords
def rover_coords(binary_img):
    # Identify nonzero pixels
    ypos, xpos = binary_img.nonzero()
    # Calculate pixel positions with reference to the rover position being at the
    # center bottom of the image.
    x_pixel = -(ypos - binary_img.shape[0]).astype(np.float)
    y_pixel = -(xpos - binary_img.shape[1]/2 ).astype(np.float)
    return x_pixel, y_pixel


# Define a function to convert to radial coords in rover space
def to_polar_coords(x_pixel, y_pixel):
    # Convert (x_pixel, y_pixel) to (distance, angle)
    # in polar coordinates in rover space
    # Calculate distance to each pixel
    dist = np.sqrt(x_pixel**2 + y_pixel**2)
    # Calculate angle away from vertical for each pixel
    angles = np.arctan2(y_pixel, x_pixel)
    return dist, angles

def polar_to_cartesian(dist, angles):
    '''Converts polar coordinates to cartesian

    angles - a list of angles in radians'''
    x = dist*np.cos(angles)
    y = dist*np.sin(angles)
    return x, y


# Define a function to map rover space pixels to world space
def rotate_pix(xpix, ypix, yaw):
    # Convert yaw to radians
    yaw_rad = yaw * np.pi / 180
    xpix_rotated = (xpix * np.cos(yaw_rad)) - (ypix * np.sin(yaw_rad))

    ypix_rotated = (xpix * np.sin(yaw_rad)) + (ypix * np.cos(yaw_rad))
    # Return the result
    return xpix_rotated, ypix_rotated

def translate_pix(xpix_rot, ypix_rot, xpos, ypos, scale):
    # Apply a scaling and a translation
    xpix_translated = (xpix_rot / scale) + xpos
    ypix_translated = (ypix_rot / scale) + ypos
    # Return the result
    return xpix_translated, ypix_translated


# Define a function to apply rotation and translation (and clipping)
# Once you define the two functions above this function should work
def pix_to_world(xpix, ypix, xpos, ypos, yaw, world_size, scale):
    # Apply rotation
    xpix_rot, ypix_rot = rotate_pix(xpix, ypix, yaw)
    # Apply translation
    xpix_tran, ypix_tran = translate_pix(xpix_rot, ypix_rot, xpos, ypos, scale)
    # Perform rotation, translation and clipping all at once
    x_pix_world = np.clip(np.int_(xpix_tran), 0, world_size - 1)
    y_pix_world = np.clip(np.int_(ypix_tran), 0, world_size - 1)
    # Return the result
    return x_pix_world, y_pix_world

# Define a function to perform a perspective transform
def perspect_transform(img, src, dst):

    M = cv2.getPerspectiveTransform(src, dst)
    warped = cv2.warpPerspective(img, M, (img.shape[1], img.shape[0]))# keep same size as input image

    return warped




####################################################################################
########################### Perception step ########################################
####################################################################################

def perception_step(Rover):
    ''' Performs rover perception

    Maps the terrain (navigagle terrain, samples, obstacles) from camera image and saves it in Rover object'''
    image = Rover.img

# 1) Define source and destination points for perspective transform
    dst_size = 5
    bottom_offset = 6
    source = np.float32([[14, 140], [301 ,140],[200, 96], [118, 96]])
    destination = np.float32([[image.shape[1]/2 - dst_size, image.shape[0] - bottom_offset],
                  [image.shape[1]/2 + dst_size, image.shape[0] - bottom_offset],
                  [image.shape[1]/2 + dst_size, image.shape[0] - 2*dst_size - bottom_offset],
                  [image.shape[1]/2 - dst_size, image.shape[0] - 2*dst_size - bottom_offset], ])

# 2) Apply perspective transform
    warped = perspect_transform(image, source, destination)

# 3) Apply color threshold to identify navigable terrain/obstacles/rock samples
    # creating mask to only take real obstacles/navigable_terrain from the camera's field of view
    im2 = np.ones_like(image)*255 #white image of size similar to input images
    im2 = perspect_transform(im2,source,destination) #white color where camera see
    mask = color_thresh(im2) #mask to only take real obstacles
    mask[0:40] = 0 # looking any further is messy, just add obstacles that are close

    navigable_terrain = color_thresh(warped)
    obstacles = color_thresh(warped, inverse= True)*mask
    rock_samples = threshed = color_thresh(warped, rgb_above = (140,110,0), rgb_below = (210,180,50), inverse = False)

# 4) Update Rover.vision_image
    Rover.vision_image[:,:,0] = obstacles*255
    Rover.vision_image[:,:,1] = rock_samples*255
    Rover.vision_image[:,:,2] = navigable_terrain*255

# 5) Convert thresholded image pixel values to rover-centric coords
    x_pix_navi, y_pix_navi = rover_coords(navigable_terrain)
    x_pix_obst, y_pix_obst = rover_coords(obstacles)
    x_pix_sample, y_pix_sample = rover_coords(rock_samples)

# 6) Convert rover-centric pixel values to world coords
    x,y = Rover.pos
    yaw = Rover.yaw
    scale = 10
    world_size = Rover.worldmap.shape[0]
    x_pix_navi_world, y_pix_navi_world = pix_to_world(x_pix_navi, y_pix_navi, x, y, yaw, world_size, scale )
    x_pix_obst_world, y_pix_obst_world = pix_to_world(x_pix_obst, y_pix_obst, x, y, yaw, world_size, scale )
    x_pix_sample_world, y_pix_sample_world = pix_to_world(x_pix_sample, y_pix_sample, x, y, yaw, world_size, scale )

# 7) Update worldmap (to be displayed on right side of screen)

    # Map world only if the rover is not inclined
    if  (Rover.pitch < 0.5 or Rover.pitch > 359.5) and (Rover.roll < 0.5 or Rover.roll >359.5):
        # add navigable terrain, make sure there is no overflow
        inc = 5 # increment
        can_increase_navigable_mask = Rover.worldmap[:,:,2] <= 255-inc
        navigable_from_img = np.zeros_like(Rover.worldmap[:,:,2], dtype='bool')
        navigable_from_img[y_pix_navi_world, x_pix_navi_world] = True
        increase_navigable = navigable_from_img & can_increase_navigable_mask
        Rover.worldmap[increase_navigable,2] += inc
        #Rover.worldmap[  y_pix_navi_world, x_pix_navi_world, 2] += 5 # blue for navigable (one should check for overflow)

        # add obstacles and samples
        Rover.worldmap[ y_pix_obst_world, x_pix_obst_world, 0] += 1 # red for obstacles
        Rover.worldmap[ y_pix_sample_world, x_pix_sample_world, 1] = 255 # green for samples
        #Rover.worldmap[int(Rover.ypos[Rover.count]),int(Rover.xpos[Rover.count]), 0] = 255 # rover position on map

# 8) Convert rover-centric pixel positions to polar coordinates
    # Update Rover pixel distances and angles

    Rover.nav_dists, Rover.nav_angles = to_polar_coords(x_pix_navi, y_pix_navi)
    Rover.obst_dists, Rover.obst_angles = to_polar_coords(x_pix_obst, y_pix_obst)
    Rover.sample_dists, Rover.sample_angles = to_polar_coords(x_pix_sample, y_pix_sample)




    return Rover
