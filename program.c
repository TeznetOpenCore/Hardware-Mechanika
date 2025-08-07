#include <gtk/gtk.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <fcntl.h>
#include <errno.h>
#include <termios.h>
#include <pthread.h>

#define SERIAL_PORT "/dev/ttyUSB0"
#define BAUD_RATE B9600

int serial_fd;
struct termios tty;
GtkTextBuffer *text_buffer;
GtkWidget *register_entry, *key_entry, *address_entry;

// Function to append text to the output buffer (text view)
void append_text_to_buffer(const char *text) {
    GtkTextIter end;
    gtk_text_buffer_get_end_iter(text_buffer, &end);
    gtk_text_buffer_insert(text_buffer, &end, text, -1);
}

// Function to send command via serial
void send_command(const char *command) {
    char command_with_crlf[256];
    snprintf(command_with_crlf, sizeof(command_with_crlf), "%s\r\n", command);
    write(serial_fd, command_with_crlf, strlen(command_with_crlf));
    char sent_msg[300];
    snprintf(sent_msg, sizeof(sent_msg), "[SENT] %s\n", command_with_crlf);
    append_text_to_buffer(sent_msg);
}

// Thread to read from the device
void *read_from_device(void *arg) {
    char buffer[256];
    int n;
    while (1) {
        n = read(serial_fd, buffer, sizeof(buffer) - 1);
        if (n > 0) {
            buffer[n] = '\0';
            append_text_to_buffer(buffer);
        }
        usleep(100000);  // Sleep for 100ms
    }
    return NULL;
}

// Function to configure the serial port
int configure_serial_port(const char *port) {
    serial_fd = open(port, O_RDWR | O_NOCTTY | O_NDELAY);
    if (serial_fd == -1) {
        perror("Unable to open serial port");
        return -1;
    }

    tcgetattr(serial_fd, &tty);

    cfsetospeed(&tty, BAUD_RATE);
    cfsetispeed(&tty, BAUD_RATE);

    tty.c_cflag &= ~PARENB;
    tty.c_cflag &= ~CSTOPB;
    tty.c_cflag &= ~CSIZE;
    tty.c_cflag |= CS8;

    tty.c_cflag &= ~CRTSCTS;
    tty.c_cflag |= (CLOCAL | CREAD);

    tty.c_lflag &= ~(ICANON | ECHO | ECHOE | ISIG);

    tty.c_cc[VMIN] = 0;
    tty.c_cc[VTIME] = 10;

    if (tcsetattr(serial_fd, TCSANOW, &tty) != 0) {
        perror("Error configuring serial port");
        return -1;
    }

    return 0;
}

// Callback when "Send Key" button is clicked
void on_send_key_button_clicked(GtkWidget *widget, gpointer data) {
    const char *register_value = gtk_entry_get_text(GTK_ENTRY(register_entry));
    const char *key_value = gtk_entry_get_text(GTK_ENTRY(key_entry));
    const char *address_value = gtk_entry_get_text(GTK_ENTRY(address_entry));

    if (strlen(register_value) == 0 || strlen(key_value) == 0 || strlen(address_value) == 0) {
        append_text_to_buffer("[ERROR] Register, Key, or Address cannot be empty!\n");
        return;
    }

    // Construct and send the AT command
    char command[256];
    snprintf(command, sizeof(command), "AT+SEND=%s,%ld,%s-%s", address_value, strlen(register_value) + strlen(key_value) + 1, register_value, key_value);
    send_command(command);
}

// Callback for "Send Manual AT Command" button
void on_send_button_clicked(GtkWidget *widget, gpointer entry) {
    const char *command = gtk_entry_get_text(GTK_ENTRY(entry));
    send_command(command);
}

int main(int argc, char *argv[]) {
    // Initialize serial port
    if (configure_serial_port(SERIAL_PORT) != 0) {
        return -1;
    }

    // Create a thread for reading the device
    pthread_t read_thread;
    pthread_create(&read_thread, NULL, read_from_device, NULL);

    // Initialize GTK
    gtk_init(&argc, &argv);

    // Create a new window
    GtkWidget *window = gtk_window_new(GTK_WINDOW_TOPLEVEL);
    gtk_window_set_title(GTK_WINDOW(window), "RYLR896 Controller");
    gtk_window_set_default_size(GTK_WINDOW(window), 400, 400);

    // Create a vertical box to hold everything
    GtkWidget *vbox = gtk_box_new(GTK_ORIENTATION_VERTICAL, 5);
    gtk_container_add(GTK_CONTAINER(window), vbox);

    // Create an entry field for AT command input
    GtkWidget *manual_command_entry = gtk_entry_new();
    gtk_box_pack_start(GTK_BOX(vbox), manual_command_entry, FALSE, FALSE, 0);

    // Create a send button
    GtkWidget *send_button = gtk_button_new_with_label("Send AT Command");
    g_signal_connect(send_button, "clicked", G_CALLBACK(on_send_button_clicked), manual_command_entry);
    gtk_box_pack_start(GTK_BOX(vbox), send_button, FALSE, FALSE, 0);

    // Create a text view to display the logs
    GtkWidget *text_view = gtk_text_view_new();
    text_buffer = gtk_text_view_get_buffer(GTK_TEXT_VIEW(text_view));
    gtk_text_view_set_editable(GTK_TEXT_VIEW(text_view), FALSE);
    gtk_box_pack_start(GTK_BOX(vbox), text_view, TRUE, TRUE, 0);

    // Create entry for address input
    address_entry = gtk_entry_new();
    gtk_entry_set_placeholder_text(GTK_ENTRY(address_entry), "Enter Address");
    gtk_box_pack_start(GTK_BOX(vbox), address_entry, FALSE, FALSE, 0);

    // Create entry for register selection
    register_entry = gtk_entry_new();
    gtk_entry_set_placeholder_text(GTK_ENTRY(register_entry), "Enter Register (EYX, EZX, EXX)");
    gtk_box_pack_start(GTK_BOX(vbox), register_entry, FALSE, FALSE, 0);

    // Create entry for key input
    key_entry = gtk_entry_new();
    gtk_entry_set_placeholder_text(GTK_ENTRY(key_entry), "Enter Key");
    gtk_box_pack_start(GTK_BOX(vbox), key_entry, FALSE, FALSE, 0);

    // Create a send key button
    GtkWidget *send_key_button = gtk_button_new_with_label("Send Key");
    g_signal_connect(send_key_button, "clicked", G_CALLBACK(on_send_key_button_clicked), NULL);
    gtk_box_pack_start(GTK_BOX(vbox), send_key_button, FALSE, FALSE, 0);

    // Show all widgets
    gtk_widget_show_all(window);

    // Connect the window close event to exit the application
    g_signal_connect(window, "destroy", G_CALLBACK(gtk_main_quit), NULL);

    // Start the GTK main loop
    gtk_main();

    // Close the serial port
    close(serial_fd);
    return 0;
}

