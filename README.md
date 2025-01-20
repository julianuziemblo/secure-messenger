# secure_messenger
A simple, secure P2P chat in Python.

## Running
### Docker
```bash
./run.sh -u <username> -P <passphrase>
```

### Locally
```bash
python3 app.py -u <username> -P <passphrase>
```

## Basic usage
### Available commands
- `/join <IP>[:<port>]` - join a conversation through a user with provided IP (and optionally also port)
- `/accept <user>` - accept user's request to join your converation
- `/list` - list users in this conversation
- `/msg <message>` - send message to all users in current conversation
- `/whisper <user> <message>` - send message to specific user in current conversation
- `/exit` - exit current conversation or the whole app 
- `/help` - display all commands 

## Description
The app uses [ssl](https://docs.python.org/3/library/ssl.html) and [`cryptography`](https://cryptography.io/en/latest/) modules to encrypt the communication end-to-end.
