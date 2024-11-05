IMAGE_NAME = avalonlee/twitch-archiver
VERSION = latest

# Build the Docker image
build:
	docker build -t $(IMAGE_NAME):$(VERSION) .

# Push the image to Docker Hub
push:
	docker push $(IMAGE_NAME):$(VERSION)

# Build and push in one command
deploy: build push

# Login to Docker Hub (run this before deploy if needed)
login:
	docker login

# Remove local image
clean:
	docker rmi $(IMAGE_NAME):$(VERSION)

.PHONY: build push deploy login clean