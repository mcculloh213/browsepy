Run Redis container:

```bash
$ docker run --name celeritas-redis -d -p 6379:6379 redis
```

Run Celery Distributed Task Worker:

```bash
$ celery -A browsepy.plugin.text_digest.celeritas.celery worker --loglevel=info &
```

Run Platform:

```bash
$ python -m browsepy --plugin file-actions --plugin text-digest
```
