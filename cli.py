import sys
import core.config as cfg
from core.cli.colors import Col

def capture_stream(stream):
    try:
        stream_data = stream.getvalue()
    except AttributeError:
        stream_data = None
    if stream_data:
        print(stream)

def custom_except_hook(exctype, value, traceback):
    print(
        f"\n{Col.RED}ERROR{Col.RESET} occured in application: ",
        end='\n')
    capture_stream(sys.stdout)
    capture_stream(sys.stderr)
    sys.stdout, sys.stderr = sys.__stdout__, sys.__stderr__
    sys.__excepthook__(exctype, value, traceback)


sys.excepthook = custom_except_hook  # noqa


def main():
    debug = cfg.debug_mode
    if 'debug' in sys.argv or '--debug' in sys.argv:
        debug = True

    serve = True if '--serve' in sys.argv else False
    if '--simple' in sys.argv or '--serve' in sys.argv:
        from core.cli.cli import CLIApp
        sys.stdout = sys.__stdout__
        sys.stderr = sys.__stderr__
        cli = CLIApp(debug=debug, silent=serve)
        cli.initialize()
        if serve:
            from perform.webapi.server import run_flask
            try:
                run_flask()
            except:
                cli.stop()
            cli.stop()
        else:
            try:
                cli.loop()
            except KeyboardInterrupt:
                print()
                cli.stop()
    else:
        import signal
        import io
        import curses
        from core.cli.tui.tui import ctrl_c_handler, TUIApp
        sys.stdout = io.StringIO()
        sys.stderr = io.StringIO()
        signal.signal(signal.SIGINT, ctrl_c_handler)
        curses.wrapper(TUIApp, debug=debug)
        curses.endwin()


if __name__ == "__main__":
    main()
