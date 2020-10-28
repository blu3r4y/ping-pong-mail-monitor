# JKU OEH Mail Monitor

A small application that sends emails to `oeh.jku.at` addresses and monitors if they are received.

## Deployment

- Place the `credentials.json` into the `data` folder after enabling the GMail API (see [here](https://developers.google.com/gmail/api/quickstart/python)).
- Rename the `config.template.json` to `config.json` and change the parameters accordingly
  - The `from_address` specifies the sender e-mail address to be used from your account
  - The `targets` holds a list of e-mail addresses which will be used for monitoring

Then, just use the already pushed [blu3r4y/jku-oeh-mail-monitor](https://hub.docker.com/r/blu3r4y/jku-oeh-mail-monitor) container:

```bash
docker run --detach \
    --name jku-oeh-mail-monitor \
    --restart always \
    --volume /path/to/your/data:/usr/src/data \
    blu3r4y/jku-oeh-mail-monitor
```

Optionally, build the container yourself with `docker build -t jku-oeh-mail-monitor .`
