#!/bin/env python3
'''

    Wake up my screen with CCE if the cinnamon screensaver turns off
     ie we stopped being idle

   You need write access to the CEC device:

   sudo usermod -G dialout ${MYUSERNAME}
   logout/login to apply

'''

import logging
import os
import subprocess
import sys
import textwrap
import time

DBUS_INTERFACE = 'org.cinnamon.ScreenSaver'

try:
    from pydbus import SystemBus, SessionBus
    from pydbus.generic import signal
except ImportError:  # pragma: no cover
    print("Please install pydbus - rpm: python-pydbus", file=sys.stderr)
    raise

try:
    from gi.repository.GLib import MainLoop
except ImportError:  # pragma: no cover
    print("Please install pygobject - rpm: python-gobject", file=sys.stderr)
    raise

try:
    from argparse import ArgumentParser
except ImportError:  # pragma: no cover
    print("Please install argparse - rpm: python-argparse", file=sys.stderr)
    raise

##########################################
def setup_args():
    '''
        Setup the argparse object.

        Make sure all fields have defaults so we could use this as an object
    '''
    parser = ArgumentParser(description=textwrap.dedent(__doc__))

    parser.add_argument('--debug',action='store_true',
                        help='Print out all debugging actions',
                        default=False)
    parser.add_argument('--dbus-use-system-bus',action='store_true',
                        help='Should we use the global SystemBus or the user SessionBus. The SystemBus requires settings in /etc/dbus-1/system.d/myservice.conf',
                        default=False)

    return parser

##########################################

##########################################
##########################################
if __name__ == '__main__':

    PARSER = setup_args()
    ARGS = PARSER.parse_args()

    MYLOGGER = logging.getLogger()

    if ARGS.debug:
        MYLOGGER.setLevel(logging.DEBUG)
    else:
        MYLOGGER.setLevel(logging.WARNING)

    handler = logging.StreamHandler(sys.stderr)
    handler.setLevel(logging.DEBUG)
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    MYLOGGER.addHandler(handler)

    PROGRAM_NAME = os.path.basename(sys.argv[0])
    MYLOGGER.debug('Running:%s args:%s', PROGRAM_NAME, sys.argv[1:])

    if ARGS.dbus_use_system_bus:
        # There is virtually no time this is the right bus
        #  for this activity
        MYLOGGER.debug('Using SYSTEM dbus')
        BUS = SystemBus()
    else:
        MYLOGGER.debug('Using SESSION dbus')
        BUS = SessionBus()

    if ARGS.dbus_use_system_bus:
        MYLOGGER.debug('Subscribing to system bus %s', DBUS_INTERFACE)
    else:
        MYLOGGER.debug('Subscribing to session bus %s', DBUS_INTERFACE)

    def signal_recieved(sender, obj, iface, signal, params):
        ''' Define in scope so I can read ARGS '''
        signal_msg = params[0]

        logging.debug("sender:%s object:%s iface:%s signal:%s all_params:%s signal_msg=%s", sender, obj, iface, signal, params, signal_msg)

        if signal != 'ActiveChanged':
            logging.debug("Not what we are looking for, ignored")
            return

        logging.debug("START OF SIGNAL PROCESSING")

        if signal_msg is True:
            logging.debug("Screensaver now active")
        else:
            logging.info("Running 'on 0\\nas\\nquit' to turn on TV")
            proc = subprocess.Popen(['/usr/bin/cec-client'], stdin=subprocess.PIPE)
            results = proc.communicate(input='on 0\nas\nquit\n'.encode())
            time.sleep(3)
            logging.debug(results[0])
            logging.debug(results[1])
            proc.terminate()
            proc.kill()

        logging.debug("END OF SIGNAL PROCESSING")


    BUS.subscribe(iface=DBUS_INTERFACE, signal_fired=signal_recieved)

    # loop forever, until CTRL+C, or something goes wrong
    try:
        MainLoop().run()
    except KeyboardInterrupt:
        logging.debug('Got CTRL+C, exiting cleanly')
        raise SystemExit

