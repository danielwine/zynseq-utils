from core.config import VERSION

MSG_HEADER = f'Zynseg interactive shell {VERSION} by danielwine. ' \
            '\nsequencer/engine library by B. Walton and J. F. Moyano' \
            '\nh: help, u: usage, x: exit, enter: previous cmd'
MSG_SERVE = f'Server {VERSION} by danielwine'
MSG_USAGE = 'Example usage:\nls\nsp 2\nan 0 40 110 200\nan 8 40 110 200\ntps 1 0'
ERR_INVALID = 'Invalid argument type. Expected'
ERR_MISSING_ARG = 'Missing argument. Expected type'
