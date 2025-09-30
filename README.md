# copilot

So you have to go to every folder and run docker build -t image_name .
then this will give the image and to run the image you can use docker run -d --name container_name -p (port_name) -e (env_variables) (If any) image_name 


# GitHub Integration Service
docker build -t myflaskapp:latest .
docker run -d --name flask-container \
  -p 8000:8000 \
  -e GITHUB_CLIENT_ID=Ov23liobtmlrvUrHpuCO \
  -e GITHUB_CLIENT_SECRET=40ac607867c28380912dbd492654f4e15b834610 \
  -e REDIRECT_URI=http://localhost:8000/github/callback \
  myflaskapp:latest

# Consistency-Checker
docker build -t consistency-checker .
docker run -d --name flask-container1 -p 5001:5000 consistency-checker

# Test Scenario Generator

docker build -t test_scenario .
docker run -d --name flask-container2 -p 5050:5001 test_scenario