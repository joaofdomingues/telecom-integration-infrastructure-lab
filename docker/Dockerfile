FROM ubuntu:24.04
RUN apt-get update && apt-get install -y cmake g++ python3 python3-pip && rm -rf /var/lib/apt/lists/*
WORKDIR /app
COPY . .
RUN mkdir build && cd build && cmake .. && make
CMD ["/app/build/telecom_integration_checker", "/app/config/telecom_nodes.csv"]
