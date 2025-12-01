#!/bin/bash

# Microservices Startup Script
# Starts all backend services for the e-commerce application

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Base directory
BASE_DIR="/Users/oleksandrshkera/Desktop/capstone/my-ecommerce-devops/services"
LOG_DIR="$BASE_DIR/logs"

# Create log directory
mkdir -p "$LOG_DIR"

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}Starting Microservices...${NC}"
echo -e "${GREEN}========================================${NC}"

# Function to wait for a service to be ready
wait_for_service() {
    local port=$1
    local service=$2
    local max_attempts=30
    local attempt=1

    echo -e "${YELLOW}Waiting for $service on port $port...${NC}"
    while ! lsof -i :$port > /dev/null 2>&1; do
        if [ $attempt -ge $max_attempts ]; then
            echo -e "${RED}✗ $service failed to start after $max_attempts seconds${NC}"
            return 1
        fi
        sleep 1
        ((attempt++))
    done
    echo -e "${GREEN}✓ $service is ready on port $port${NC}"
}

# 1. Start Product Catalog Service (Go) - Port 3550
echo -e "\n${YELLOW}[1/9] Starting Product Catalog Service...${NC}"
cd "$BASE_DIR/productcatalogservice"
PORT=3550 ./productcatalogservice > "$LOG_DIR/productcatalog.log" 2>&1 &
wait_for_service 3550 "Product Catalog Service"

# 2. Start Currency Service (Node.js) - Port 7001
echo -e "\n${YELLOW}[2/9] Starting Currency Service...${NC}"
cd "$BASE_DIR/currencyservice"
PORT=7001 node server.js > "$LOG_DIR/currency.log" 2>&1 &
wait_for_service 7001 "Currency Service"

# 3. Start Cart Service (C#/.NET) - Port 5000
echo -e "\n${YELLOW}[3/9] Starting Cart Service...${NC}"
cd "$BASE_DIR/cartservice/src"
dotnet run > "$LOG_DIR/cart.log" 2>&1 &
wait_for_service 5000 "Cart Service"

# 4. Start Shipping Service (Go) - Port 50051
echo -e "\n${YELLOW}[4/9] Starting Shipping Service...${NC}"
cd "$BASE_DIR/shippingservice"
PORT=50051 ./shippingservice > "$LOG_DIR/shipping.log" 2>&1 &
wait_for_service 50051 "Shipping Service"

# 5. Start Payment Service (Node.js) - Port 50052
echo -e "\n${YELLOW}[5/9] Starting Payment Service...${NC}"
cd "$BASE_DIR/paymentservice"
PORT=50052 node index.js > "$LOG_DIR/payment.log" 2>&1 &
wait_for_service 50052 "Payment Service"

# 6. Start Email Service (Python) - Port 6000
echo -e "\n${YELLOW}[6/9] Starting Email Service...${NC}"
cd "$BASE_DIR/emailservice"
PORT=6000 AWS_REGION=us-east-1 SENDER_EMAIL=noreply@example.com python email_server.py > "$LOG_DIR/email.log" 2>&1 &
wait_for_service 6000 "Email Service"

# 7. Start Recommendation Service (Python) - Port 8080
echo -e "\n${YELLOW}[7/9] Starting Recommendation Service...${NC}"
cd "$BASE_DIR/recommendationservice"
PORT=8080 PRODUCT_CATALOG_SERVICE_ADDR=localhost:3550 python recommendation_server.py > "$LOG_DIR/recommendation.log" 2>&1 &
wait_for_service 8080 "Recommendation Service"

# 8. Start Checkout Service (Go) - Port 5050
echo -e "\n${YELLOW}[8/9] Starting Checkout Service...${NC}"
cd "$BASE_DIR/checkoutservice"
PORT=5050 \
SHIPPING_SERVICE_ADDR=localhost:50051 \
PRODUCT_CATALOG_SERVICE_ADDR=localhost:3550 \
CART_SERVICE_ADDR=localhost:5000 \
CURRENCY_SERVICE_ADDR=localhost:7001 \
EMAIL_SERVICE_ADDR=localhost:6000 \
PAYMENT_SERVICE_ADDR=localhost:50052 \
./checkoutservice > "$LOG_DIR/checkout.log" 2>&1 &
wait_for_service 5050 "Checkout Service"

# 9. Start Frontend (Go) - Port 9000
echo -e "\n${YELLOW}[9/9] Starting Frontend...${NC}"
cd "$BASE_DIR/frontend"
PORT=9000 \
PRODUCT_CATALOG_SERVICE_ADDR=localhost:3550 \
CURRENCY_SERVICE_ADDR=localhost:7001 \
CART_SERVICE_ADDR=localhost:5000 \
RECOMMENDATION_SERVICE_ADDR=localhost:8080 \
CHECKOUT_SERVICE_ADDR=localhost:5050 \
SHIPPING_SERVICE_ADDR=localhost:50051 \
AD_SERVICE_ADDR=localhost:9555 \
SHOPPING_ASSISTANT_SERVICE_ADDR=localhost:8081 \
./frontend > "$LOG_DIR/frontend.log" 2>&1 &
wait_for_service 9000 "Frontend"

echo -e "\n${GREEN}========================================${NC}"
echo -e "${GREEN}All services started successfully!${NC}"
echo -e "${GREEN}========================================${NC}"

echo -e "\n${YELLOW}Service Endpoints:${NC}"
echo "  Product Catalog:    http://localhost:3550"
echo "  Currency:           http://localhost:7001"
echo "  Cart:               http://localhost:5000"
echo "  Shipping:           http://localhost:50051"
echo "  Payment:            http://localhost:50052"
echo "  Email:              http://localhost:6000"
echo "  Recommendation:     http://localhost:8080"
echo "  Checkout:           http://localhost:5050"
echo -e "  ${GREEN}Frontend (Web UI):  http://localhost:9000${NC}"

echo -e "\n${YELLOW}Logs are available in: $LOG_DIR${NC}"

echo -e "\n${YELLOW}To stop all services, run:${NC}"
echo "  pkill -f productcatalogservice && pkill -f 'node server.js' && pkill -f 'dotnet run' && pkill -f shippingservice && pkill -f 'node index.js' && pkill -f email_server.py && pkill -f recommendation_server.py && pkill -f checkoutservice"

echo -e "\n${GREEN}Ready to start frontend!${NC}"
