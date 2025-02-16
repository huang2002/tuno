# tuno

> UNO right in your terminal, with both server and client.

## Installation

1. Switch to an environment compatible with Python 3.12 or higher.
2. Install [`pipx`](https://pipx.pypa.io/stable/) if you have not.
3. Install this app using `pipx`:

    ```sh
    pipx install tuno
    ```

## Usage

1. Start a game server for players to join:

    ```sh
    tuno server
    ```

2. Copy the server address printed in console and share it to all the players.
3. Start a game client and join the game: (You may keep the server terminal run
    in background and open another terminal session to join the game.)

    ```sh
    tuno client
    ```

4. Enjoy the game with your friends!

## Build from Source

```sh
hatch build
```

## Links

- [Github Repo](https://github.com/huang2002/tuno)
- [LICENSE (ISC)](./LICENSE)
