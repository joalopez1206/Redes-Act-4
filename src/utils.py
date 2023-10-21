def contains_end_of_message(message, end_sequence):
    return message.endswith(end_sequence)
 
 
def remove_end_of_message(full_message, end_sequence):
    index = full_message.rfind(end_sequence)
    return full_message[:index]

def receive_full_mesage(connection_socket, buff_size, end_sequence):
    recv_message = connection_socket.recv(buff_size)
    full_message = recv_message
    is_end_of_message = contains_end_of_message(full_message.decode(), end_sequence)
    while not is_end_of_message:
        recv_message = connection_socket.recv(buff_size)

        full_message += recv_message

        is_end_of_message = contains_end_of_message(full_message.decode(), end_sequence)
    full_message = remove_end_of_message(full_message.decode(), end_sequence)
    return full_message.encode()