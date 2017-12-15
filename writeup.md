## Project: Search and Sample Return
### Writeup Template: You can use this file as a template for your writeup if you want to submit it as a markdown file, but feel free to use some other method and submit a pdf if you prefer.

---


**The goals / steps of this project are the following:**  

**Training / Calibration**  

* Download the simulator and take data in "Training Mode"
* Test out the functions in the Jupyter Notebook provided
* Add functions to detect obstacles and samples of interest (golden rocks)
* Fill in the `process_image()` function with the appropriate image processing steps (perspective transform, color threshold etc.) to get from raw images to a map.  The `output_image` you create in this step should demonstrate that your mapping pipeline works.
* Use `moviepy` to process the images in your saved dataset with the `process_image()` function.  Include the video you produce as part of your submission.

**Autonomous Navigation / Mapping**

* Fill in the `perception_step()` function within the `perception.py` script with the appropriate image processing functions to create a map and update `Rover()` data (similar to what you did with `process_image()` in the notebook).
* Fill in the `decision_step()` function within the `decision.py` script with conditional statements that take into consideration the outputs of the `perception_step()` in deciding how to issue throttle, brake and steering commands.
* Iterate on your perception and decision function until your rover does a reasonable (need to define metric) job of navigating and mapping.  

[//]: # (Image References)

[image1]: ./misc/rover_image.jpg
[image2]: ./calibration_images/example_grid1.jpg
[image3]: ./calibration_images/example_rock1.jpg
[image4]: ./calibration_images/example.jpg
[image5]: ./calibration_images/rd.jpg
[image6]: ./calibration_images/to.jpg
[image7]: ./output/better-run.jpg

## [Rubric](https://review.udacity.com/#!/rubrics/916/view) Points
### Here I will consider the rubric points individually and describe how I addressed each point in my implementation.  

---
### Writeup / README

#### 1. Provide a Writeup / README that includes all the rubric points and how you addressed each one.  You can submit your writeup as markdown or pdf.  

You're reading it!

### Notebook Analysis
#### 1. Run the functions provided in the notebook on test images (first with the test data provided, next on data you have recorded). Add/modify functions to allow for color selection of obstacles and rock samples.

In this part I looked closer at all the functions I am supposed to use and checked them for various inputs. After that I modified `color_tresh` function. Two capabilites were added to it:
* inversion of resulting image (for obstacle detection)
* getting pixels that are in specyfic range or rgb (for sample rock detection)

**New funciton is backwards compatilbe so the code to detect obstacles does not have to be changed.**
Below one can see an exemplary image and results of obstacle and sample detection by `color_tresh` function:

![Before thresholding][image4]

![Rock detection. RGB range: 120<r<230 90<g<200 0<b<70 )][image5]

![Obstacle detection][image6]

One must note that if perspective transform is done before tresholding, than output image needs to be masked appropriately. Otherwise the regions not seen by the rover camera would be treated as obstacle.


#### 1. Populate the `process_image()` function with the appropriate analysis steps to map pixels identifying navigable terrain, obstacles and rock samples into a worldmap.  Run `process_image()` on your test data using the `moviepy` functions provided to create video output of your result.

The following steps were coded inside `process_image()` function:
1. Defining source points based on grid image and destination point based on chosen locations in the output image.
1. Applying perspective transform on image captured by rover camera.
1. Applying color thresholding to detect navigable terrain, rock samples and obstacles. **For obstacles an additional mask is created to not consider points that cannot be seen from rover camera, and points too far away from the rover. This prevents some additional obstacles detection on navigable terrain.**
1. Converting thresholded image pixel values to rover-centric coordinates.
1. Converting rover-centric pixel values to world coordinates
1. Updating world map. **Special consideration is undertaken to not allow for pixel value overflow when increasing its value.**
1. Making mosaic image based on analysis outputs.

The results of the analysis can be seen in *./output/test_mapping.mp4*

### Autonomous Navigation and Mapping

#### 1. Fill in the `perception_step()` (at the bottom of the `perception.py` script) and `decision_step()` (in `decision.py`) functions in the autonomous mapping scripts and an explanation is provided in the writeup of how and why these functions were modified as they were.

1. `perception_step()`:
Funcition is similar to the one used in the jupyter notebook with few changes
* **Added condition for mapping if the rover is not leaning, because the perspective transform is only accurate when the rover is straight**
* **Added transform to polar coordinates for obstacles, navigable terrain and sample rocks. The transformed data is sent to the Rover for control.**

1. `decision_step()`:
* **In starting (forward) mode the direction of movement is chosen as a weighted sum of mean navigable angle and navigable angle which is the most to the left. The weighting coefficient (`left_coeff`) is increasing over time to make rover go closer to the left wall. This way allows rover to map the whole terrain and find 5-6 samples depending on time of run.**
* If the rover has very little navigable terrain in front of it, rover starts to turn to find more navigable terrain (stop mode)
* **If rover got stuck (very low velocity for more than 2 seconds) it's mode changes to stuck stop, in which it rotates 15* in the right direction.**
* **If the rover is very close to the sample, it brakes**


#### 2. Launching in autonomous mode your rover can navigate and map autonomously.  Explain your results and how you might improve them in your writeup.  

* First solution (find-samples branch) allows for mapping of about 40-60% with about 60% fidelity and localizing 1-2 rock samples.
* The improved solution described above (master branch) allows to map almost whole world (96%) with better fidelity (76%) and find 5 (sometimes 6) samples. It can also pick up rock if the rover bumps directly into them (1-2 rocks for run). This solution makes the rover bump into obstacle more often the basic solution so mode for braking free was added.

![Improved algorithm run outcome][image7]

To improve algorithm one should:
* Improve the algorithm for going by the wall. For example one could find direction which is most to the left and has at leas 1-2 meters of navigable terrain.
* Check for obstacles in front of the rover and add a mode for circling them (instead of bumping into tem).
* Instead of turning everything below the threshold in the image into obstacle on map, one could only make obstacles to pixels behind the navigable (possible by edge detection algorithm). In other case small obstacles on the way can tern into prolonged obstacles on map as they are not flat and perspective transform does not work correct for them.

##### My framerate was: 38, graphics quality: good and resolution: 720x480
