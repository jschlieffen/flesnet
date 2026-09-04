import curses


def calculator(stdscr):
    curses.curs_set(1)

    # Enable mouse support
    curses.mousemask(curses.ALL_MOUSE_EVENTS)

    # Colors
    curses.start_color()
    curses.init_pair(1, curses.COLOR_WHITE, curses.COLOR_BLUE)
    curses.init_pair(2, curses.COLOR_GREEN, curses.COLOR_BLACK)
    curses.init_pair(3, curses.COLOR_RED, curses.COLOR_BLACK)

    height, width = stdscr.getmaxyx()

    field_width = 10
    x = (width - field_width) // 2
    y = (height - 8) // 2

    fields = [
        ("First number:", y + 2),
        ("Second number:", y + 4),
    ]

    # Default values
    values = ["0", "0"]

    current_field = 0
    result = 0
    error = None

    while True:
        stdscr.clear()

        # Title
        title = "Addition Calculator"
        stdscr.addstr(
            y,
            (width - len(title)) // 2,
            title,
            curses.A_BOLD
        )

        # Draw fields
        for i, (label, field_y) in enumerate(fields):

            label_x = x - len(label) - 2

            stdscr.addstr(
                field_y,
                label_x,
                label
            )

            # Blue background
            stdscr.addstr(
                field_y,
                x,
                " " * field_width,
                curses.color_pair(1)
            )

            # Number
            stdscr.addstr(
                field_y,
                x + 1,
                values[i][:field_width - 2],
                curses.color_pair(1)
            )

        # Result
        if error is None:
            result_text = f"Result: {result:g}"

            stdscr.addstr(
                y + 6,
                (width - len(result_text)) // 2,
                result_text,
                curses.color_pair(2) | curses.A_BOLD
            )
        else:
            stdscr.addstr(
                y + 6,
                (width - len(error)) // 2,
                error,
                curses.color_pair(3)
            )

        # Instructions
        instruction = "Click a field to edit • Enter to calculate • Q to quit"

        stdscr.addstr(
            y + 8,
            (width - len(instruction)) // 2,
            instruction,
            curses.A_DIM
        )

        # Cursor
        cursor_x = x + 1 + len(values[current_field])

        stdscr.move(
            fields[current_field][1],
            min(cursor_x, x + field_width - 2)
        )

        stdscr.refresh()

        key = stdscr.getch()

        # -------------------------
        # Mouse click
        # -------------------------
        if key == curses.KEY_MOUSE:

            try:
                _, mouse_x, mouse_y, _, mouse_state = curses.getmouse()

                if mouse_state & curses.BUTTON1_CLICKED:

                    for i, (_, field_y) in enumerate(fields):

                        if (
                            field_y == mouse_y
                            and x <= mouse_x < x + field_width
                        ):
                            current_field = i
                            error = None

            except curses.error:
                pass

        # -------------------------
        # Enter = ALWAYS calculate
        # -------------------------
        elif key in (curses.KEY_ENTER, 10, 13):

            try:
                number1 = float(values[0])
                number2 = float(values[1])

                result = number1 + number2
                error = None

            except ValueError:

                error = "Please enter valid numbers!"

        # -------------------------
        # Backspace
        # -------------------------
        elif key in (curses.KEY_BACKSPACE, 127, 8):

            values[current_field] = values[current_field][:-1]

            # Empty field becomes 0
            if values[current_field] == "":
                values[current_field] = "0"

            error = None

        # -------------------------
        # Numbers / decimal / minus
        # -------------------------
        elif 32 <= key <= 126:

            char = chr(key)

            if char.isdigit() or char in ".-":

                # If the field currently contains the default 0,
                # replace it when typing a number.
                if values[current_field] == "0" and char.isdigit():
                    values[current_field] = char
                else:
                    if len(values[current_field]) < field_width - 2:
                        values[current_field] += char

                error = None

        # -------------------------
        # Quit
        # -------------------------
        elif key in (ord("q"), ord("Q")):
            break


if __name__ == "__main__":
    curses.wrapper(calculator)