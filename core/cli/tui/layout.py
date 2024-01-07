
def get_layout(mx, my):
    return {
        'standard': {
            'footer': [1, mx, my, 0, 5, 10],
            'console': [1, int(mx / 2) - 1, my - 2, 0, 1, 10]
        },
        'message': {
            'messages': [
                int(my / 2) + 1, int(mx / 2) - 3, 22, 1, 7, 10]
        },
        'data': {
            'status': [1, int(mx / 1.6), 0, 0, 2, 11],
            'status2': [1, int(mx / 2)-1, 0, int(mx/1.6), 2, 11],
            'window2': [20, int(mx / 4), 2, int(mx/4), 3, 10]
        },
        'sequence': {
            'sequences': [20, int(mx / 4), 2, 1, 3, 10],
        },
        'pattern': {
            'pattern': [my - 3, int(mx / 2), 2, int(mx / 2), 4, 10]
        }
    }
