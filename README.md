# JKU OEH Mail Monitor

A small application that sends mails to `oeh.jku.at` addresses and monitors if they are received.

See the live results at [jku-oeh-mail-monitor.mario.ac](http://jku-oeh-mail-monitor.mario.ac/).

## Deployment

- You need two GMail accounts ("ping" & "pong"), [create an API key](https://developers.google.com/gmail/api/quickstart/python) for each and store the `credentials.json` to
  - `data/credentils.ping.json` for the account that sends mails
  - `data/credentils.pong.json` for the account that receives mails
- Rename the `config.template.json` to `config.json` and change the parameters accordingly
  - `auth_method` Either `server` (opens a local web server that for the OAuth callback - for local development) or `console` (requires console interaction - for production servers)
  - `pings_per_hour` Amount of mails that shall be sent to each account per hour (maximum: 60)
  - `receive_timeout` Amount of minutes to wait for an mail to be received again
  - `targets` A list of mail addresses which will receive mails for monitoring

Finally, just use the already pushed [blu3r4y/jku-oeh-mail-monitor](https://hub.docker.com/r/blu3r4y/jku-oeh-mail-monitor) container

```bash
docker run --detach \
    --name jku-oeh-mail-monitor \
    --restart always \
    --volume /path/to/your/data:/usr/src/data \
    blu3r4y/jku-oeh-mail-monitor
```

Optionally, build the container yourself with `docker build -t jku-oeh-mail-monitor .`
