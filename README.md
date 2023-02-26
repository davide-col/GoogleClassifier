# GoogleClassifier# NLP CEFR Classification

## Installation

- Create a virtual environment and activate it:

```
$ virtualenv -p python3 .env
$ source .env/bin/activate
```

- Install the requirements:

```
$ pip3 install -r requirements.txt
```

## Usage

```bash
$ cd src
$ ./run_all_experiments.sh
```

## Build Docker Image

```bash
$ cd '<chemin source projet>'
$ export DOCKER_BUILDKIT=0    
$ docker build --no-cache -t docker_image .
```

## Run Docker Image

```bash
$ docker run -d -p 5000:5000 -ti --rm --name='docker_image' docker_image:latest
```

## Export Docker Image

```bash
$ docker save docker_image:latest > docker_image.tar
```

## Load Docker Image Archive

```bash
$ docker load < docker_image.tar
```

