#!/usr/bin/env python3
import sys
import traceback
import argparse
import os
import os.path
import urllib.parse
import tkinter as tk
import io
import termios
import contextlib
import datetime
from getpass import _raw_input, fallback_getpass

log_enabled = os.environ.get('PINENTRY_TREZOR_LOG_PATH')
dontflash = os.environ.get('PINENTRY_TREZOR_DONT_FLASH') == '1'
conf_keysets = os.environ.get('PINENTRY_TREZOR_KEYSET')
dont_explain = os.environ.get('PINENTRY_TREZOR_DONT_EXPLAIN') == '1'
force_message = os.environ.get('PINENTRY_TREZOR_FORCE_MESSAGE')


all_keysets = ['123456789']
if conf_keysets:
    all_keysets.append(conf_keysets)
else:
    all_keysets.extend(['xcvsdfwer', 'm,.jkluio'])

_log = None


def resp(text):
    print(text)
    try:
        sys.stdout.flush()
    except BrokenPipeError:
        pass


def log(text):
    if not _log:
        return
    _log.write('[{}] {}\n'.format(datetime.datetime.now().isoformat(), text))
    _log.flush()


def log_e():
    if not _log:
        return
    _log.write('[{}] '.format(datetime.datetime.now().isoformat()))
    traceback.print_exc(file=_log)
    _log.write('\n')
    _log.flush()


def tty_entry(tty_name, prompt):
    # Copied from https://github.com/python/cpython/blob/3.6/Lib/getpass.py
    # Make tty configurable, derive defaults from None
    tty_name = tty_name or '/dev/tty'
    stream = None
    passwd = None
    with contextlib.ExitStack() as stack:
        try:
            # Always try reading and writing directly on the tty first.
            fd = os.open(tty_name, os.O_RDWR | os.O_NOCTTY)
            tty = io.FileIO(fd, 'w+')
            stack.enter_context(tty)
            input = io.TextIOWrapper(tty)
            stack.enter_context(input)
            if not stream:
                stream = input
        except OSError as e:
            # If that fails, see if stdin can be controlled.
            stack.close()
            try:
                fd = sys.stdin.fileno()
            except (AttributeError, ValueError):
                fd = None
                passwd = fallback_getpass(prompt, stream)
            input = sys.stdin
            if not stream:
                stream = sys.stderr

        if fd is not None:
            try:
                old = termios.tcgetattr(fd)     # a copy to save
                new = old[:]
                new[3] &= ~termios.ECHO  # 3 == 'lflags'
                tcsetattr_flags = termios.TCSAFLUSH
                if hasattr(termios, 'TCSASOFT'):
                    tcsetattr_flags |= termios.TCSASOFT
                try:
                    termios.tcsetattr(fd, tcsetattr_flags, new)
                    passwd = _raw_input(prompt, stream, input=input)
                finally:
                    termios.tcsetattr(fd, tcsetattr_flags, old)
                    stream.flush()  # issue7208
            except termios.error:
                if passwd is not None:
                    # _raw_input succeeded.  The final tcsetattr failed.  Reraise  # noqa
                    # instead of leaving the terminal in an unknown state.
                    raise
                # We can't control the tty or stdin.  Give up and use normal IO.  # noqa
                # fallback_getpass() raises an appropriate warning.
                if stream is not input:
                    # clean up unused file objects before blocking
                    stack.close()
                passwd = fallback_getpass(prompt, stream)

        stream.write('\n')
        return passwd


def tk_entry(title, message, error):
    root = tk.Tk()

    pin = []

    def do_clear(*pargs, **kwargs):
        del pin[:]

        if not dontflash:
            button = buttons['clear']
            button.configure(text='*Clear*')

            def reset():
                button.configure(text='Clear')

            button.after(100, reset)

    _done = []

    def done(*pargs, **kwargs):
        _done.append(True)
        root.destroy()

    root.bind('<Return>', done)
    root.bind('<Escape>', lambda *p, **k: root.destroy())
    root.bind('<BackSpace>', do_clear)

    buttons = {}

    def entry(value):
        pin.append(value)

        if not dontflash:
            button = buttons[value]
            button.configure(text='X')

            def reset():
                button.configure(text=' ')

            button.after(100, reset)

    for keyset in all_keysets:
        for k, i in zip(keyset, '123456789'):
            root.bind(k, lambda e, i=i: entry(i))

    frame = tk.Frame(root)
    frame.master.title(title)
    frame.pack()
    tk.Label(
        frame,
        text=message,
        wraplength='10cm',
        justify='left',
    ).pack()
    if error:
        tk.Label(
            frame,
            text=error,
            fg='red',
            wraplength='10cm',
            justify='left',
        ).pack()

    buttons_frame = tk.Frame(frame)
    for i, v in enumerate('789456123'):
        button = tk.Button(
            buttons_frame,
            text=' ',
            width=3,
            height=3,
            command=lambda v=v: entry(v),
        )
        buttons[v] = button
        button.grid(
            row=int(i / 3),
            column=i % 3,
            padx=3,
            pady=3,
        )
    buttons_frame.pack()

    actions = tk.Frame(frame)
    tk.Button(
        actions, text='Done', command=done
    ).pack(side='right')
    buttons['clear'] = tk.Button(
        actions, text='Clear', command=do_clear
    )
    buttons['clear'].pack(side='right')
    tk.Button(
        actions, text='Cancel', command=root.destroy
    ).pack(side='right')
    actions.pack(padx=3, pady=3)

    tk.mainloop()
    if not _done:
        raise RuntimeError('Canceled by user')

    return ''.join(pin)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--display', help='Override X11 display')
    args = parser.parse_args()
    if args.display:
        os.environ['DISPLAY'] = args.display

    if log_enabled:
        global _log
        _log = open(log_enabled, 'w')

    try:
        resp('OK')

        title = 'GPG: Enter Trezor PIN'
        message = ''
        error = ''
        tty = '/dev/tty'
        for line in sys.stdin:
            splits = line.split(' ', 1)
            command = splits.pop(0).strip()
            rest = splits.pop(0).strip() if splits else None
            log('Command [{}] rest [{}]'.format(command, rest))
            if not command or command in (
                        'SETPROMPT',
                        'SETQUALITYBAR',
                        'SETQUALITYBAR_TT',
                        'SETREPEATERROR',
                        'SETREPEAT',
                        'SETOK',
                        'SETCANCEL',
                    ):
                pass
            elif command == 'SETDESC':
                message = urllib.parse.unquote(rest)
            elif command == 'SETERROR':
                error = rest
            elif command == 'SETTITLE':
                title = rest
            elif command == 'OPTION':
                if rest.startswith('ttyname='):
                    tty = rest.split('=', 1)[-1]  # noqa
                elif rest.startswith('display='):
                    os.environ['DISPLAY'] = rest.split('=', 1)[-1]
            elif command == 'GETINFO':
                pass
            elif command == 'SETKEYINFO':
                pass
            elif command == 'GETPIN':
                if force_message:
                    message = force_message
                if os.environ.get('DISPLAY'):
                    value = tk_entry(title, message, error)
                else:
                    prompt = message
                    if error:
                        prompt = prompt + '\nERROR: {}'.format(error)
                    if not dont_explain:
                        prompt += '\nThe keys in these grids correspond to the grid displayed on your Trezor:'  # noqa
                        prompt += '\n{}'.format(
                            '   '.join(
                                ' '.join(
                                    keyset[9 - 3 * (row + 1):9 - 3 * row]
                                ) for keyset in all_keysets
                            ) for row in range(3)
                        )
                    prompt += '\nEnter PIN: '
                    value = tty_entry(tty, prompt)
                resp('D {}'.format(value))
                error = ''
            elif command == 'CONFIRM':
                pass
            elif command == 'BYE':
                pass
            else:
                log('WARNING: Unknown command [{}] args [{}]'.format(
                    command, rest))
            resp('OK')
    except:  # noqa
        log_e()


if __name__ == '__main__':
    main()
