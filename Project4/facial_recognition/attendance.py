def track_attendance(input_file, output_file):
    try:
        # Read the input file
        with open(input_file, "r") as infile:
            lines = infile.readlines()

        # Parse the input file
        date = lines[0].strip()  # The first line is the date
        attendance_data = {}
        for line in lines[1:]:
            name, status = line.strip().split(":")
            attendance_data[name.strip()] = int(status.strip())

        # Initialize or read the output file
        try:
            with open(output_file, "r") as outfile:
                output_lines = outfile.readlines()
        except FileNotFoundError:
            output_lines = []

        # Process cumulative attendance and dates
        cumulative_attendance = {}
        dates = []
        attendance_count = 0
        in_dates_section = False

        # Parse existing data from the output file
        for line in output_lines:
            if ": " in line and not line.startswith("Attendance Count:"):
                name, total = line.strip().split(": ")
                cumulative_attendance[name.strip()] = int(total.strip())
            elif line.startswith("Attendance Count:"):
                attendance_count = int(line.split(":")[1].strip())
            elif line.strip() == "Dates:":
                in_dates_section = True
            elif in_dates_section and line.strip():
                dates.append(line.strip())

        # Check if the date is already in the output file (avoid double counting)
        if date in dates:
            print(f"Attendance for {date} has already been recorded. No updates made.")
            return

        # Update attendance totals
        for name, status in attendance_data.items():
            cumulative_attendance[name] = cumulative_attendance.get(name, 0) + status

        # Update attendance count and dates
        attendance_count += 1
        dates.append(date)

        # Write updated data back to the output file
        with open(output_file, "w") as outfile:
            # Write cumulative attendance
            for name, total in cumulative_attendance.items():
                outfile.write(f"{name}: {total}\n")

            # Write attendance count
            outfile.write(f"Attendance Count: {attendance_count}\n")

            # Ensure the `Dates:` header is present
            outfile.write("Dates:\n")

            # Append all dates
            for d in dates:
                outfile.write(f"{d}\n")

        print("Attendance successfully tracked and updated.")
    except Exception as e:
        print(f"An error occurred: {e}")

# Example usage
input_file = "attendance_input.txt"  # Replace with your input file path
output_file = "attendance_output.txt"  # Replace with your output file path
track_attendance(input_file, output_file)
