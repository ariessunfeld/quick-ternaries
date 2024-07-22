"""Exception hook for better catch-all display of errors"""

import sys
import traceback

from .error_reporter import send_error_log_via_email

from PySide6.QtWidgets import QMessageBox, QPushButton


def exception_handler(exc_type, exc_value, exc_traceback):

    MAX_LEN = 500
    # Format the exception message
    full_exception_message = "".join(traceback.format_exception(exc_type, exc_value, exc_traceback))
    
    # Truncate the message to the last 200 characters
    if len(full_exception_message) > MAX_LEN:
        exception_message = '...' + full_exception_message[-MAX_LEN:]
    else:
        exception_message = full_exception_message
    
    # Create a message box to display the exception
    msg_box = QMessageBox()
    msg_box.setIcon(QMessageBox.Critical)
    msg_box.setWindowTitle("An Unexpected Error Occurred")
    msg_box.setText("An unexpected error occurred. Please see the details below.")
    msg_box.setDetailedText(exception_message)
    msg_box.setStandardButtons(QMessageBox.Ok)
    
    send_button = QPushButton("Send Log")
    msg_box.addButton(send_button, QMessageBox.ActionRole)

    def send_log():
        detailed_message = full_exception_message  # Send more detailed log if needed
        subject = "Error Log from Quick Ternaries"
        success = send_error_log_via_email(subject, detailed_message)
        if success:
            QMessageBox.information(None, "Success", "Error log sent successfully!")
        else:
            QMessageBox.warning(None, "Failure", "Failed to send error log.")

    send_button.clicked.connect(send_log)

    msg_box.exec()
    
    # Call the default excepthook if needed
    sys.__excepthook__(exc_type, exc_value, exc_traceback)
