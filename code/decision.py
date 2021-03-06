import numpy as np


# This is where you can build a decision tree for determining throttle, brake and steer
# commands based on the output of the perception_step() function
def decision_step(Rover):

    # Implement conditionals to decide what to do given perception data
    # Here you're all set up with some basic functionality but you'll need to
    # improve on this decision tree to do a good job of navigating autonomously!

    # Example:
    # Check if we have vision data to make decisions with
    if Rover.nav_angles is not None:
        # Check for Rover.mode status
        if Rover.mode == 'forward':
            # Check the extent of navigable terrain
            if Rover.near_sample:
                Rover.throttle = 0
                Rover.brake = Rover.brake_set
                Rover.steer = 0
            else:
                if np.abs(Rover.vel) > 0.1:
                    Rover.start_forward_time = Rover.total_time
                if Rover.start_forward_time is not None:
                    if Rover.total_time - Rover.start_forward_time > 2:
                        Rover.mode = 'stuck stop'
                        Rover.stuck_yaw = Rover.yaw

                if len(Rover.nav_angles) >= Rover.stop_forward:
                    # If mode is forward, navigable terrain looks good
                    # and velocity is below max, then throttle
                    if Rover.vel < Rover.max_vel:
                        # Set throttle value to throttle setting
                        Rover.throttle = Rover.throttle_set
                    else: # Else coast
                        Rover.throttle = 0
                    Rover.brake = 0
                    # Set steering to average angle clipped to the range +/- 15
                    mean_angle = np.mean(Rover.nav_angles * 180/np.pi)
                    right_angle = np.max(Rover.nav_angles) * 180/np.pi
                    Rover.steer = np.clip(10*(mean_angle*(1-Rover.left_coeff) + right_angle*Rover.left_coeff), -15, 15)
                    if Rover.left_coeff < 0.35:
                        Rover.left_coeff += 0.0005
                    #print(Rover.left_coeff)
                    # Stay close to the right wall:
                    # take direction which has at least Rover.min_freeway*0.1m of navigable terrain in front and is the most to the right
                    # allowed_ways = Rover.nav_dists > Rover.min_freeway
                    # allowed_angles = Rover.nav_angles[allowed_ways]
                    # Rover.steer = np.clip( np.min(allowed_angles)*180/np.pi, -15, 15)

                # If there's a lack of navigable terrain pixels then go to 'stop' mode
                elif len(Rover.nav_angles) < Rover.stop_forward:
                        # Set mode to "stop" and hit the brakes!
                        Rover.throttle = 0
                        # Set brake to stored brake value
                        Rover.brake = Rover.brake_set
                        Rover.steer = 0
                        Rover.mode = 'stop'



        # If we're already in "stop" mode then make different decisions
        elif Rover.mode == 'stop':
            Rover.left_coeff = 0.25
            # If we're in stop mode but still moving keep braking
            if Rover.vel > 0.2:
                Rover.throttle = 0
                Rover.brake = Rover.brake_set
                Rover.steer = 0
            # If we're not moving (vel < 0.2) then do something else
            elif Rover.vel <= 0.2:
                # Now we're stopped and we have vision data to see if there's a path forward
                if len(Rover.nav_angles) < Rover.go_forward:
                    Rover.throttle = 0
                    # Release the brake to allow turning
                    Rover.brake = 0
                    # Turn range is +/- 15 degrees, when stopped the next line will induce 4-wheel turning
                    Rover.steer = -15 # Could be more clever here about which way to turn
                # If we're stopped but see sufficient navigable terrain in front then go!
                if len(Rover.nav_angles) >= Rover.go_forward:
                    # Set throttle back to stored value
                    Rover.throttle = Rover.throttle_set
                    # Release the brake
                    Rover.brake = 0
                    # Set steer to mean angle
                    Rover.steer = np.clip(np.mean(Rover.nav_angles * 180/np.pi), -15, 15)
                    Rover.start_forward_time = Rover.total_time
                    Rover.mode = 'forward'

        # if the rover gets stuck
        elif Rover.mode == 'stuck stop':
            Rover.steer = -15
            Rover.brake = 0
            Rover.throttle = 0

            if np.abs(Rover.stuck_yaw - Rover.yaw) >15:
                Rover.mode = 'forward'
                Rover.start_forward_time = Rover.total_time

        # if the rover "sees" sample
        #elif Rover.mode == 'sample approach':


    print(Rover.left_coeff, Rover.mode)


    # If in a state where want to pickup a rock send pickup command
    if Rover.near_sample and Rover.vel == 0 and not Rover.picking_up:
        Rover.send_pickup = True

    return Rover
