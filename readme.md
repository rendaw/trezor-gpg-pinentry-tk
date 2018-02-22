# Trezor-style PIN entry for GPG

This is an alternate PIN entry for use with [trezor-agent]() or for people with number-only PINs.  It displays a grid of unlabeled buttons and supports configurable keyboard mappings, by default allowing entry via these grids:

```
w e r      u i o      7 8 9
s d f      j k l      4 5 6
x c v      m , .      1 2 3
```

### Installation

1. Run `pip install trezor-gpg-pinentry-tk`
2. Find where it's installed with by running `which trezor-gpg-pinentry-tk`
3. Add this line to `$GPGHOME/gpg-agent.conf`: `pinentry-program /path/to/trezor_gpg`
4. Run `echo RELOADAGENT | gpg-connect-agent` or restart your computer

### Configuration

Set these environment variables on your `gpg-agent` daemon, by overriding `/usr/lib/systemd/user/gpg-agent.service` for example.

* **PINENTRY_TREZOR_LOG_PATH** = `/path/to/log/file`.  Enable logging and write logs to `/path/to/log/file`
* **PINENTRY_TREZOR_DONT_FLASH** = `1`.  Don't show which keypad button was pressed when using the keyboard.
* **PINENTRY_TREZOR_KEYSET** = `123456789`.  Use this letter grid for keyboard entry.
* **PINENTRY_TREZOR_DONT_EXPLAIN** = `1`.  Don't explain or show the grid when entering via TTY.
