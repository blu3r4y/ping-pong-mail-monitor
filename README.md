# Ping Pong Mail Monitor

[![AGPL 3.0 License](https://img.shields.io/badge/License-AGPL%203.0-yellow?style=popout-square)](LICENSE.txt)
[![GitHub Latest Release](https://img.shields.io/github/v/release/blu3r4y/ping-pong-mail-monitor?style=popout-square)](https://github.com/blu3r4y/ping-pong-mail-monitor/releases/latest)
[![GitHub Workflow Status](https://img.shields.io/github/actions/workflow/status/blu3r4y/ping-pong-mail-monitor/build-container-images.yml?branch=v1.0.1&style=popout-square)](https://github.com/blu3r4y/ping-pong-mail-monitor/actions)
[![Docker Pulls](https://img.shields.io/docker/pulls/blu3r4y/ping-pong-mail-monitor.svg?style=popout-square)](https://hub.docker.com/r/blu3r4y/ping-pong-mail-monitor)
[![Docker Image Size](https://img.shields.io/docker/image-size/blu3r4y/ping-pong-mail-monitor?style=popout-square)](https://hub.docker.com/r/blu3r4y/ping-pong-mail-monitor)
![Supported Platforms](https://img.shields.io/badge/platforms-amd64%20%7C%20arm64-lightgrey?style=popout-square)

![Icon](src/static/favicon.png)

An application that sends mails to one or more addresses and monitors if they are correctly bounced backed to another address.
Initially inspired to monitor a flaky mail server of the OEH JKU.

![Dashboard Screenshot](dashboard.png)

## Configuration and deployment

1. Create two GMail accounts ("ping" & "pong").
2. Create an OAuth API credentials (see below) for each and store the `credentials.json` that you can download from the developer console to
    - `data/credentils.ping.json` for the account that will send mails
    - `data/credentils.pong.json` for the account that will receive mails
3. Next, rename the `config.template.json` to `config.json` and change the parameters accordingly.

| Configuration              | Default                 | Description |
|----------------------------|-------------------------|-------------|
| `auth_method`              | `console`               | Either `server` (opens a local web server for the initial OAuth callback - for local development) or `console` (requires console interaction - for production servers where you can not easily open sockets on the fly) |
| `pings_per_hour`           | `6`                     | Number of mails that shall be sent per target and hour (maximum: `60`) |
| `receive_timeout`          | `1440`                  | Minutes to wait for an mail to be received before it is declared as expired |
| `prefix`                   | `#PINGPONGMAILMONITOR#` | Text that is prepended to every subject line in all mails |
| `targets`                  | `[]`                    | Mail addresses to which we will shall send mails |
| `revoke_expired`           | `true`                  | This will check expired mails again even after the timeout, but only once |
| `revoke_expired_per_pings` | `300`                   | If `requeue_expired` is `true`, the number of pings per target, after which we check expired mails again, once |
| `default_dashboard_days`   | `30`                    | The number of recent days that will be shown and cached on the dashboard |

Finally, run the [blu3r4y/ping-pong-mail-monitor](https://hub.docker.com/r/blu3r4y/ping-pong-mail-monitor) container and access the dashboard at http://localhost:8080

```bash
docker run --detach \
    --name ping-pong-mail-monitor \
    --restart always \
    -p 8080:80 \
    -v /path/to/your/data:/usr/src/data \
    -e API_TOKEN=CHANGE-ME-TO-SOMETHING-SECRET \
    blu3r4y/ping-pong-mail-monitor
```

You can also use the supplied [`docker-compose.yml`](docker-compose.yml)

    docker-compose up -d

Alternatively, build the container yourself with

    docker build -t ping-pong-mail-monitor .

### Initial authentication flow on a server

To complete the initial authentication flow on a server start the container once like so

```bash
sudo docker run --rm -it \
    --volume /path/to/your/data:/usr/src/data \
    blu3r4y/ping-pong-mail-monitor /bin/bash -c 'python /usr/src/app/monitor.py'
```

This will create tokens in `data/token.ping.pickle` and `data/token.pong.pickle` on success.

### OAuth API Credentials

For each of the two GMail accounts ("ping" & "pong") create OAuth API credentials in the Google Cloud Console.

1. If you haven't already, create a new project
2. Go to the "APIs & Services" section
3. Go to the "Credentials" section
4. Click on "Create credentials" and select "OAuth client ID" with type "Desktop app"

Next, we need to change the OAuth consent screen to be in testing mode.
Access to sensitive scopes like GMail usually require a special verifiction process, unless you are in testing mode.

1. Go to the "OAuth consent screen" section
2. Ensure that the "Publishing status" is set to "Testing"
3. Invite your GMail user (usually the same as the account you are using) as a test user to the project

### Web API

To add or remove targets easily, you can access the exposed API on http://localhost:80/api as long as you configured the `API_TOKEN` environment variable as well.

## Attribution

Favicon made by [Freepik](https://www.flaticon.com/authors/freepik) from [Flaticon](https://www.flaticon.com/).
Laptop Mockup made by [Rawpixel](https://www.rawpixel.com/) from [Freepik](http://freepik.com/).
