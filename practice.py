'''
This is the script for practice session (Selection and Integration in Orientational averaging)
'''

# import library
from datetime import datetime
from psychopy import visual, event, monitors, core,logging, gui
import math
import numpy as np
import math
import os
import pandas as pd
import sys
import pylink
import time
import random

# eyelink related library
from EyeLinkCoreGraphicsPsychoPy import EyeLinkCoreGraphicsPsychoPy
from string import ascii_letters, digits
import platform

# clear command output and start logging
os.system('cls' if os.name == 'ht' else 'clear')
logging.console.setLevel(logging.CRITICAL)
print("**************************************")
print("EXPERIMENT 1.2: ENSEMBLE PERCEPTION PRACTICE BLOCK")
print("PSYCHOPY LOGGING set to : CRITICAL")
print(datetime.now())
print("**************************************")

# set global key for quitting
event.globalKeys.clear()
event.globalKeys.add(key='q', modifiers = ['ctrl', 'alt'], func=os._exit, func_args=[1], func_kwargs=None)

current_date = datetime.now().strftime("%Y%m%d")
current_time = datetime.now().strftime("%H%M%S")

# get observer's info
info = gui.Dlg(title="EXPERIMENT 1.2: ENSEMBLE PERCEPTION PRACTICE BLOCK", pos = [600, 300],
               labelButtonOK="READY", labelButtonCancel="LEAVE",
               )
info.addText("PRACTICE BLOCK\n\n")
info.addText("\nExperimenter Check")
info.addField('Experiment Date (YMD): ', current_date)
info.addField('Experiment Time (HMS): ', current_time)
info.addField('Participant No.: ')
info.addField('View Condition: ', choices = ['Please Select', 'Foveal', 'Peripheral', 'Full'])
info.addField('Block: ', choices = ['Please Select', 1000, 2500])
show_info = info.show()

if isinstance(show_info[4], int) == False or show_info[3] == 'Please Select':
    error = gui.Dlg(title="ERROR", pos = [600,300])
    error.addText("Please select the block information and try again!")
    error.show()
    sys.exit()



# create data directory, check info and save file name
try:
    os.mkdir('practice_trial_data')
    print("Directory Created")
except FileExistsError:
    print("Directory already Exist!")
if info.OK:
    save_file_name = 'practice_trial_data/' + show_info[0] + show_info[1] + '_P' + \
        show_info[2] + '_' + str(show_info[3]) + '_view_' + str(show_info[4]) + 'ms_practice_trial.csv'
else:
    print("User Cancelled")
save_path = gui.fileSaveDlg(initFileName=save_file_name,
                            prompt = 'Select Save File'
                            )

# ----------------------------------------------------------------------------
# eye tracking code pylink setup (folder setting)
use_retina = False
dummy_mode = False
edf_fname = 'P01'
dlg_title = 'Enter EDF File Name'
dlg_prompt = 'Please enter a file name with 8 or fewer characters\n' + \
             '[letters, numbers, and underscore].'

# loop until we get a valid filename
while True:
    dlg = gui.Dlg(dlg_title)
    dlg.addText(dlg_prompt)
    dlg.addField('File Name:', edf_fname)
    # show dialog and wait for OK or Cancel
    ok_data = dlg.show()
    if dlg.OK:  # if ok_data is not None
        print('EDF data filename: {}'.format(ok_data[0]))
    else:
        print('user cancelled')
        core.quit()
        sys.exit()

    # get the string entered by the experimenter
    tmp_str = dlg.data[0]
    # strip trailing characters, ignore the ".edf" extension
    edf_fname = tmp_str.rstrip().split('.')[0]

    # check if the filename is valid (length <= 8 & no special char)
    allowed_char = ascii_letters + digits + '_'
    if not all([c in allowed_char for c in edf_fname]):
        print('ERROR: Invalid EDF filename')
    elif len(edf_fname) > 8:
        print('ERROR: EDF filename should not exceed 8 characters')
    else:
        break

# Set up a folder to store the EDF data files and the associated resources
# e.g., files defining the interest areas used in each trial
results_folder = 'practice_eyetracking_data'
if not os.path.exists(results_folder):
    os.makedirs(results_folder)

# We download EDF data file from the EyeLink Host PC to the local hard
# drive at the end of each testing session, here we rename the EDF to
# include session start date/time
time_str = time.strftime("_%Y_%m_%d_%H_%M", time.localtime())
session_identifier = edf_fname + time_str

# # create a folder for the current testing session in the "results" folder
# session_folder = os.path.join(results_folder, session_identifier)
# if not os.path.exists(session_folder):
#     os.makedirs(session_folder)

# eyetracking setup end (folder setting)
# ----------------------------------------------------------------------------

# ----------------------------------------------------------------------------
# eyetracking setup (Connect, Setting, Calibration)

# Step 1: Connect to the EyeLink Host PC
#
# The Host IP address, by default, is "100.1.1.1".
# the "el_tracker" objected created here can be accessed through the Pylink
# Set the Host PC address to "None" (without quotes) to run the script
# in "Dummy Mode"
if dummy_mode:
    el_tracker = pylink.EyeLink(None)
else:
    try:
        el_tracker = pylink.EyeLink("100.1.1.1")
    except RuntimeError as error:
        print('ERROR:', error)
        core.quit()
        sys.exit()

# Step 2: Open an EDF data file on the Host PC
edf_file = edf_fname + ".EDF"
try:
    el_tracker.openDataFile(edf_file)
except RuntimeError as err:
    print('ERROR:', err)
    # close the link if we have one open
    if el_tracker.isConnected():
        el_tracker.close()
    core.quit()
    sys.exit()
# Add a header text to the EDF file to identify the current experiment name
# This is OPTIONAL. If your text starts with "RECORDED BY " it will be
# available in DataViewer's Inspector window by clicking
# the EDF session node in the top panel and looking for the "Recorded By:"
# field in the bottom panel of the Inspector.
preamble_text = 'RECORDED BY %s' % os.path.basename(__file__)
el_tracker.sendCommand("add_file_preamble_text '%s'" % preamble_text)

# Step 3: Configure the tracker
#
# Put the tracker in offline mode before we change tracking parameters
el_tracker.setOfflineMode()
# Get the software version:  1-EyeLink I, 2-EyeLink II, 3/4-EyeLink 1000,
# 5-EyeLink 1000 Plus, 6-Portable DUO
eyelink_ver = 5  # set version to 0, in case running in Dummy mode
if not dummy_mode:
    vstr = el_tracker.getTrackerVersionString()
    eyelink_ver = int(vstr.split()[-1].split('.')[0])
    # print out some version info in the shell
    print('Running experiment on %s, version %d' % (vstr, eyelink_ver))

# File and Link data control
# what eye events to save in the EDF file, include everything by default
file_event_flags = 'LEFT,RIGHT,FIXATION,SACCADE,BLINK,MESSAGE,BUTTON,INPUT'
# what eye events to make available over the link, include everything by default
link_event_flags = 'LEFT,RIGHT,FIXATION,SACCADE,BLINK,BUTTON,FIXUPDATE,INPUT'
# what sample data to save in the EDF data file and to make available
# over the link, include the 'HTARGET' flag to save head target sticker
# data for supported eye trackers
if eyelink_ver > 3:
    file_sample_flags = 'LEFT,RIGHT,GAZE,HREF,RAW,AREA,HTARGET,GAZERES,BUTTON,STATUS,INPUT'
    link_sample_flags = 'LEFT,RIGHT,GAZE,GAZERES,AREA,HTARGET,STATUS,INPUT'
else:
    file_sample_flags = 'LEFT,RIGHT,GAZE,HREF,RAW,AREA,GAZERES,BUTTON,STATUS,INPUT'
    link_sample_flags = 'LEFT,RIGHT,GAZE,GAZERES,AREA,STATUS,INPUT'
el_tracker.sendCommand("file_event_filter = %s" % file_event_flags)
el_tracker.sendCommand("file_sample_data = %s" % file_sample_flags)
el_tracker.sendCommand("link_event_filter = %s" % link_event_flags)
el_tracker.sendCommand("link_sample_data = %s" % link_sample_flags)

# Optional tracking parameters
# Sample rate, 250, 500, 1000, or 2000, check your tracker specification
# if eyelink_ver > 2:
#     el_tracker.sendCommand("sample_rate 1000")
# Choose a calibration type, H3, HV3, HV5, HV13 (HV = horizontal/vertical),
el_tracker.sendCommand("calibration_type = HV9")
# Set a gamepad button to accept calibration/drift check target
# You need a supported gamepad/button box that is connected to the Host PC
el_tracker.sendCommand("button_function 5 'accept_target_fixation'")

# Step 4: set up a graphics environment for calibration
#
# Open a window, be sure to specify monitor parameters

#  define monitor information and setup window
monitor_name = 'testMonitor'
view_distance = 105
screen_width = 54.37
screen_resolution = [1920,1080]

mon = monitors.Monitor(monitor_name)
mon.setSizePix((1920, 1080))
mon.setWidth(screen_width)
mon.setDistance(view_distance)
mon.saveMon()

win = visual.Window(size=screen_resolution, color='#C0C0C0',
                    fullscr=True, monitor=mon, allowGUI=True,
                    allowStencil=True, units='pix'
                    # screen=0
                   )
win.mouseVisible = False

#  define gaze window information, disabled at start
gaze_window = visual.Aperture(win=win, shape='circle',
                              size=(142.38,143.9), units='pix'
                             )
gaze_window.enabled = False
view_condition = show_info[3]

# get the native screen resolution used by PsychoPy
scn_width, scn_height = win.size
# resolution fix for Mac retina displays
if 'Darwin' in platform.system():
    if use_retina:
        scn_width = int(scn_width/2.0)
        scn_height = int(scn_height/2.0)

# Pass the display pixel coordinates (left, top, right, bottom) to the tracker
# see the EyeLink Installation Guide, "Customizing Screen Settings"
el_coords = "screen_pixel_coords = 0 0 %d %d" % (scn_width - 1, scn_height - 1)
el_tracker.sendCommand(el_coords)

# Write a DISPLAY_COORDS message to the EDF file
# Data Viewer needs this piece of info for proper visualization, see Data
# Viewer User Manual, "Protocol for EyeLink Data to Viewer Integration"
dv_coords = "DISPLAY_COORDS  0 0 %d %d" % (scn_width - 1, scn_height - 1)
el_tracker.sendMessage(dv_coords)

# Configure a graphics environment (genv) for tracker calibration
genv = EyeLinkCoreGraphicsPsychoPy(el_tracker, win)
print(genv)  # print out the version number of the CoreGraphics library

# Set background and foreground colors for the calibration target
# in PsychoPy, (-1, -1, -1)=black, (1, 1, 1)=white, (0, 0, 0)=mid-gray
foreground_color = (-1, -1, -1)
background_color = win.color
genv.setCalibrationColors(foreground_color, background_color)

# Set up the calibration target
#
# The target could be a "circle" (default), a "picture", a "movie" clip,
# or a rotating "spiral". To configure the type of calibration target, set
# genv.setTargetType to "circle", "picture", "movie", or "spiral", e.g.,
# genv.setTargetType('picture')
#
# Use gen.setPictureTarget() to set a "picture" target
# genv.setPictureTarget(os.path.join('images', 'fixTarget.bmp'))
#
# Use genv.setMovieTarget() to set a "movie" target
# genv.setMovieTarget(os.path.join('videos', 'calibVid.mov'))

# Use a picture as the calibration target
genv.setTargetType('picture')
genv.setPictureTarget(os.path.join('images', 'fixTarget.bmp'))

# Configure the size of the calibration target (in pixels)
# this option applies only to "circle" and "spiral" targets
# genv.setTargetSize(24)

# Beeps to play during calibration, validation and drift correction
# parameters: target, good, error
#     target -- sound to play when target moves
#     good -- sound to play on successful operation
#     error -- sound to play on failure or interruption
# Each parameter could be ''--default sound, 'off'--no sound, or a wav file
genv.setCalibrationSounds('', '', '')

# resolution fix for macOS retina display issues
if use_retina:
    genv.fixMacRetinaDisplay()

# Request Pylink to use the PsychoPy window we opened above for calibration
pylink.openGraphicsEx(genv)

# eyetracking setup ended (Connect, Setting)
# ----------------------------------------------------------------------------

# ----------------------------------------------------------------------------
# Experiment Setup
# define timing variables
fixation_time = 0.5
blank_time = 0.25
blank_iti_time = 1
set_duration = show_info[4] / 1000
frame_rate = 60

# generate stimuli triallist and shuffle
stimulus_list = [f'images/practice_set/img_{i+1}.png' for i in range(8)]
np.random.shuffle(stimulus_list)

# array for the output file
date_array = []
time_array = []
parti_no_array = []
view_condition_array = []
duration_array = []
trial_no_array = []
image_array = []
percept_ori_array = []
tuning_duration_array = []


# Functions for experiment
def fixation_cross():
    fix_hori = visual.Rect(win = win, width=0.9, height=0.1, units='deg',
                           lineColor='black', fillColor='black', pos=(0,0)
                           )
    fix_vert = visual.Rect(win = win, width=0.1, height=0.9, units='deg',
                           lineColor='black', fillColor='black', pos=(0,0)
                           )
    fix_hori.draw()
    fix_vert.draw()


def ensemble_boundary():
    boundary = visual.Circle(win=win, edges=1000, radius=4.8, lineColor='red',
                             fillColor=None, lineWidth=20, units='deg'
                             )
    boundary.draw()


def gabor_tuning():
    grating = visual.GratingStim(win = win, units= 'deg',tex='sin',
                                 mask='gauss', ori=0, pos=(0, 0),
                                 size=(3.2,3.2), sf=1.5, opacity = 1,
                                 blendmode='avg', texRes=128,
                                 interpolate=True, depth=0.0
                                 )

    event.clearEvents()
    mouse = event.Mouse()
    mouse.getWheelRel()
    start_time = core.getTime()
    while not event.getKeys(['space']):
        if abs(grating.ori) <= 90:
            wheel_dX, wheel_dY = mouse.getWheelRel()

            # for fine adjustment with scroll wheel
            grating.setOri(wheel_dY * 1, '+')

            # for coarse adjustment with keyboard f and j key
            if event.getKeys(['f']):
                grating.setOri(5, '-')
            elif event.getKeys(['j']):
                grating.setOri(5, '+')

        # to prevent the tuning to exceed 90
        else:
            if grating.ori > 0:
                grating.setOri(90)
            else:
                grating.setOri(-90)
        grating.draw()
        win.flip()
    tune_time = core.getTime() - start_time
    return grating.ori, tune_time


def instruction(view_con):

    instruct_1 = "\
Welcome to our experiment!\
\n\n\
This experiment is about orientation averaging. Each trial will begin with a fixation cross \
+. A set of orientation patches will then be shown (orientation set). \
Afterwards, A single orientation patch will be shown and you will need to adjust this orientation patch \
to the AVERAGE of the orientation set. The next trial will begin after you have confirmed the adjustment. \
"
    instruct_2 = "\
To adjust the orientation, use the keyboard 'f' and 'j' button for coarse tuning and \
use the scroll wheel ('down' and 'up') for fine tuning. You may press the button or scroll \
the wheel multiple times as long as it is within the 180 degree range. When you have done with the \
tuning, press spacebar to confirm the adjustment and the next trial will continue. \
You may try the tuning with the orientation patch below. \
"
    instruct_3a = "\
In the upcoming experimental block, you will be seeing the set \
WITHOUT RESTRCTION. \n\n\
Please be reminded to keep your sight within the set of patches for the given duration.\
"
    instruct_3b = "\
In the upcoming experimental block, you will be seeing the set \
THROUGH A WINDOW. The window will only allow you to see 1 patch at a time and the \
window will move according to where you're looking. \
A Red Boundary, which denotes the size of the whole set, will be presented. \n\n\
Please be reminded to keep your sight within the red boundary for the given duration.\
"
    instruct_3c = "\
In the upcoming experimental block, you will be seeing the set \
WITH THE FOVEA OCCLUDED. That is, the patch that you're looking at will disappear.\n\n\
Please be reminded to keep your sight within the set of patches for the given duration.\
"
    instruct_4 = "\
You will now go through an 8-trial practice. After the practice, you will have \
a 56-trial experimental block. \n\n\
If you have no questions, you may press spacebar to start the practice block. \
"

    instruct_text = visual.TextStim(win=win, font = 'Consolas', bold = False,
                                    height = 0.5, units = 'deg', color='#000000',
                                    wrapWidth = 20
                                    )
    instruct_text.setText(instruct_1)
    instruct_text.draw()
    win.flip()
    instruct_resp = event.waitKeys(maxWait=1000, keyList=['space'],
                                   clearEvents=True
                                   )

    instruct_grating = visual.GratingStim(win = win, units= 'deg',tex='sin',
                                          mask='gauss', ori=0, pos=(0, -4.5),
                                          size=(3.2,3.2), sf=1.5, opacity = 1,
                                          blendmode='avg', texRes=128,
                                          interpolate=True, depth=0.0
                                        )

    event.clearEvents()
    mouse = event.Mouse()
    mouse.getWheelRel()
    start_time = core.getTime()
    while not event.getKeys(['space']):
        instruct_text.setText(instruct_2)
        instruct_text.setPos((0,1.5))
        instruct_text.draw()
        if abs(instruct_grating.ori) <= 90:
            wheel_dX, wheel_dY = mouse.getWheelRel()

            # for fine adjustment with scroll wheel
            instruct_grating.setOri(wheel_dY * 1, '+')

            # for coarse adjustment with keyboard f and j key
            if event.getKeys(['f']):
                instruct_grating.setOri(5, '-')
            elif event.getKeys(['j']):
                instruct_grating.setOri(5, '+')

        # to prevent the tuning to exceed 90
        else:
            if instruct_grating.ori > 0:
                instruct_grating.setOri(90)
            else:
                instruct_grating.setOri(-90)
        instruct_grating.draw()
        win.flip()
    tune_time = core.getTime() - start_time

    if view_con == 'Full':
        instruct_text.setText(instruct_3a)
    elif view_con == 'Foveal':
        instruct_text.setText(instruct_3b)
    elif view_con == 'Peripheral':
        instruct_text.setText(instruct_3c)
    instruct_text.setPos((0,0))
    instruct_text.draw()
    win.flip()
    instruct_resp = event.waitKeys(maxWait=1000, keyList=['space'],
                                   clearEvents=True
                                   )

    instruct_text.setText(instruct_4)
    instruct_text.setPos((0,0))
    instruct_text.draw()
    win.flip()
    instruct_resp = event.waitKeys(maxWait=1000, keyList=['space'],
                                   clearEvents=True
                                   )

    win.flip()
    core.wait(2)


# ----------------------------------------------------------------------------
# eyetracking setup (Calibration, Helper Function)
def clear_screen(win):
    """ clear up the PsychoPy window"""

    win.fillColor = genv.getBackgroundColor()
    win.flip()


def show_msg(win, text, wait_for_keypress=True):
    """ Show task instructions on screen"""

    msg = visual.TextStim(win, text,
                          # color=genv.getForegroundColor(),
                          color = '#FFFFFF',
                          wrapWidth=scn_width/2)
    clear_screen(win)
    msg.draw()
    win.flip()

    # wait indefinitely, terminates upon any key press
    if wait_for_keypress:
        event.waitKeys()
        clear_screen(win)


def terminate_task():
    """ Terminate the task gracefully and retrieve the EDF data file

    file_to_retrieve: The EDF on the Host that we would like to download
    win: the current window used by the experimental script
    """

    el_tracker = pylink.getEYELINK()

    if el_tracker.isConnected():
        # Terminate the current trial first if the task terminated prematurely
        error = el_tracker.isRecording()
        if error == pylink.TRIAL_OK:
            abort_trial()

        # Put tracker in Offline mode
        el_tracker.setOfflineMode()

        # Clear the Host PC screen and wait for 500 ms
        el_tracker.sendCommand('clear_screen 0')
        pylink.msecDelay(500)

        # Close the edf data file on the Host
        el_tracker.closeDataFile()

        # Show a file transfer message on the screen
        msg = 'EDF data is transferring from EyeLink Host PC...'
        show_msg(win, msg, wait_for_keypress=False)

        # Download the EDF data file from the Host PC to a local data folder
        # parameters: source_file_on_the_host, destination_file_on_local_drive
        local_edf = os.path.join('practice_eyetracking_data/' + session_identifier + '.EDF')
        try:
            el_tracker.receiveDataFile(edf_file, local_edf)
        except RuntimeError as error:
            print('ERROR:', error)

        # Close the link to the tracker.
        el_tracker.close()

    # close the PsychoPy window
    win.close()

    # quit PsychoPy
    core.quit()
    sys.exit()


def abort_trial():
    """Ends recording """

    el_tracker = pylink.getEYELINK()

    # Stop recording
    if el_tracker.isRecording():
        # add 100 ms to catch final trial events
        pylink.pumpDelay(100)
        el_tracker.stopRecording()

    # clear the screen
    clear_screen(win)
    # Send a message to clear the Data Viewer screen
    bgcolor_RGB = (116, 116, 116)
    el_tracker.sendMessage('!V CLEAR %d %d %d' % bgcolor_RGB)

    # send a message to mark trial end
    el_tracker.sendMessage('TRIAL_RESULT %d' % pylink.TRIAL_ERROR)

    return pylink.TRIAL_ERROR


# eyetracking setup ended (Calibration, Helper Function)
# ----------------------------------------------------------------------------


def run_trials(trial_no, image_name):
    # preload stimuli
    set_frame = set_duration * frame_rate
    ensemble_stimuli = visual.ImageStim(win=win, image=image_name)

# ----------------------------------------------------------------------------
# eye tracking recording set up
    # get a reference to the currently active EyeLink connection
    el_tracker = pylink.getEYELINK()
    # put the tracker in the offline mode first
    el_tracker.setOfflineMode()
    # clear the host screen before we draw the backdrop
    el_tracker.sendCommand('clear_screen 0')
    # send a "TRIALID" message to mark the start of a trial, see Data
    # Viewer User Manual, "Protocol for EyeLink Data to Viewer Integration"
    el_tracker.sendMessage('TRIALID %d' % trial_no)
    # record_status_message : show some info on the Host PC
    # here we show how many trial has been tested
    status_msg = 'TRIAL number %d' % trial_no
    el_tracker.sendCommand("record_status_message '%s'" % status_msg)
    # drift check
    # we recommend drift-check at the beginning of each trial
    # the doDriftCorrect() function requires target position in integers
    # the last two arguments:
    # draw_target (1-default, 0-draw the target then call doDriftCorrect)
    # allow_setup (1-press ESCAPE to recalibrate, 0-not allowed)
    #
    # Skip drift-check if running the script in Dummy Mode
    while not dummy_mode:
        # terminate the task if no longer connected to the tracker or
        # user pressed Ctrl-C to terminate the task
        if (not el_tracker.isConnected()) or el_tracker.breakPressed():
            terminate_task()
            return pylink.ABORT_EXPT

        # drift-check and re-do camera setup if ESCAPE is pressed
        try:
            error = el_tracker.doDriftCorrect(int(scn_width/2.0),
                                              int(scn_height/2.0), 1, 1)
            # break following a success drift-check
            if error is not pylink.ESC_KEY:
                break
        except:
            pass
    # put tracker in idle/offline mode before recording
    el_tracker.setOfflineMode()

# ----------------------------------------------------------------------------
    # Start recording
    # arguments: sample_to_file, events_to_file, sample_over_link,
    # event_over_link (1-yes, 0-no)
    try:
        el_tracker.startRecording(1, 1, 1, 1)
    except RuntimeError as error:
        print("ERROR:", error)
        abort_trial()
        return pylink.TRIAL_ERROR
    # Allocate some time for the tracker to cache some samples
    pylink.pumpDelay(100)

    # determine which eye(s) is/are available
    # 0-left, 1-right, 2-binocular
    eye_used = el_tracker.eyeAvailable()
    if eye_used == 1:
        el_tracker.sendMessage("EYE_USED 1 RIGHT")
    elif eye_used == 0 or eye_used == 2:
        el_tracker.sendMessage("EYE_USED 0 LEFT")
        eye_used = 0
    else:
        print("ERROR: Could not get eye information!")
        abort_trial()
        return pylink.TRIAL_ERROR
# ----------------------------------------------------------------------------

    # fixation screen
    el_tracker.sendMessage('fixation')
    for frameN in range(int(fixation_time * frame_rate)):
        fixation_cross()
        win.flip()

    # stimuli screen
    el_tracker.sendMessage('stimuli_onset')

    # Stimuli - foveal view (restricted periphery)
    if view_condition == 'Foveal':
        win.setColor('#b0b0b0')
        for frameN in range(int(set_frame)):
            # grab the newest sample (Eye Gaze Info)
            dt = el_tracker.getNewestSample()
            if dt is None:  # no sample data
                gaze_pos = (-32768, -32768)
            else:
                if eye_used == 1 and dt.isRightSample():
                    gaze_pos = dt.getRightEye().getGaze()
                elif eye_used == 0 and dt.isLeftSample():
                    gaze_pos = dt.getLeftEye().getGaze()
            # update the window position and redraw the screen
            gaze_window.enabled = True
            gaze_window.pos = (int(gaze_pos[0]-scn_width/2.0),
                               int(scn_height/2.0-gaze_pos[1]))
            ensemble_stimuli.draw()
            gaze_window.enabled = False
            ensemble_boundary()
            win.flip()
            # Send the current position of the gaze_contingent window
            # to the tracker to record in the EDF data file
            win_pos = (int(gaze_pos[0]), int(gaze_pos[1]))
            el_tracker.sendMessage('gc_pos %d %d' % win_pos)
        gaze_window.enabled = False

    # Stimuli - peripheral view (restricted foveal)
    elif view_condition == 'Peripheral':
        win.setColor('#b0b0b0')
        for frameN in range(int(set_frame)):
            # grab the newest sample (Eye Gaze Info)
            dt = el_tracker.getNewestSample()
            if dt is None:  # no sample data
                gaze_pos = (-32768, -32768)
            else:
                if eye_used == 1 and dt.isRightSample():
                    gaze_pos = dt.getRightEye().getGaze()
                elif eye_used == 0 and dt.isLeftSample():
                    gaze_pos = dt.getLeftEye().getGaze()
            # update the window position and redraw the screen
            gaze_window.inverted = True
            gaze_window.enabled = True
            gaze_window.pos = (int(gaze_pos[0]-scn_width/2.0),
                               int(scn_height/2.0-gaze_pos[1]))
            ensemble_stimuli.draw()
            gaze_window.enabled = False
            win.flip()
            # Send the current position of the gaze_contingent window
            # to the tracker to record in the EDF data file
            win_pos = (int(gaze_pos[0]), int(gaze_pos[1]))
            el_tracker.sendMessage('gc_pos %d %d' % win_pos)
        gaze_window.enabled = False

    # Stimuli - full view (unrestricted)
    elif view_condition == 'Full':
        for frameN in range(int(set_frame)):
            ensemble_stimuli.draw()
            win.flip()
    win.setColor('#C0C0C0')

    # Stimuli offset screen
    el_tracker.sendMessage('stimuli_offset')
    for frameN in range(int(blank_time*frame_rate)):
        win.flip()

    # Tuning, ITI
    el_tracker.sendMessage('Tuning')
    percept_ori, tune_time = gabor_tuning()
    win.flip()
    core.wait(blank_iti_time)
    percept_ori_array.append(percept_ori)
    tuning_duration_array.append(tune_time)

    pylink.pumpDelay(100)
    el_tracker.stopRecording()
    # Stop recording
# ----------------------------------------------------------------------------

# ----------------------------------------------------------------------------
# Calibration Procedure
# Step 5: Set up the camera and calibrate the tracker

def calibration():
# Show the task instructions
    task_msg = 'In the task, you may press the SPACEBAR to end a trial\n' + \
        '\nPress Ctrl-C to if you need to quit the task early\n'
    if dummy_mode:
        task_msg = task_msg + '\nNow, press ENTER to start the task'
    else:
        task_msg = task_msg + '\nNow, press ENTER twice to calibrate tracker'
    show_msg(win, task_msg)

# skip this step if running the script in Dummy Mode
    if not dummy_mode:
        try:
            el_tracker.doTrackerSetup()
        except RuntimeError as err:
            print('ERROR:', err)
            el_tracker.exitCalibration()


def main():
    instruction(view_condition)
    calibration()
    # Run Experimental Trials
    for trial_no in range(len(stimulus_list)):
        date_array.append(show_info[0])
        time_array.append(show_info[1])
        parti_no_array.append(show_info[2])
        view_condition_array.append(view_condition)
        duration_array.append(show_info[4])
        trial_no_array.append(trial_no + 1)
        image_array.append(stimulus_list[trial_no])

        run_trials(trial_no, stimulus_list[trial_no])

        # output data
        outputfile = pd.DataFrame({'exp_date': date_array,
                                   'exp_time': time_array,
                                   'parti_no': parti_no_array,
                                   'view_condition': view_condition_array,
                                   'stimuli_duration': duration_array,
                                   'trial_no': trial_no_array,
                                   'image_no': image_array,
                                   'resp': percept_ori_array,
                                   'latency': tuning_duration_array,
                                   })
        outputfile.to_csv(save_path, sep=',', index=False)

    # Step 7: disconnect, download the EDF file, then terminate the task
    terminate_task()

if __name__ == "__main__":
    main()

