###This is a RESTful API for Yahoo! NSFW image detection. See [Yahoo! NSFW](https://github.com/yahoo/open_nsfw)

Build a caffe docker image (CPU) 
```
docker build -t caffe:cpu ./docker/Dockerfile
```

Check the caffe installation
```
docker run caffe:cpu caffe --version
caffe version 1.0.0-rc3
```

Run the docker image with a volume mapped to your `open_nsfw` repository. Your `test_image.jpg` should be located in this same directory.
```
git clone https://github.com/yahoo/open_nsfw.git
cd open_nsfw
docker run -p 8080:8080 --volume=$(pwd):/workspace --volume=/data/tmp/image:/data/tmp/image caffe:cpu python ./classify_nsfw.py
```

Then you can check whether an image is pornographic via 
```
http://localhost:8080/porn_image?url=YOUR_IMAGE_URL
```

