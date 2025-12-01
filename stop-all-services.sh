#!/bin/bash

# Microservices Stop Script
# Stops all running backend services

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${YELLOW}Stopping all microservices...${NC}"

# Kill all service processes
pkill -f productcatalogservice 2>/dev/null && echo -e "${GREEN}✓ Stopped Product Catalog Service${NC}" || echo -e "${YELLOW}  Product Catalog Service not running${NC}"
pkill -f "node server.js" 2>/dev/null && echo -e "${GREEN}✓ Stopped Currency Service${NC}" || echo -e "${YELLOW}  Currency Service not running${NC}"
pkill -f "dotnet run" 2>/dev/null && echo -e "${GREEN}✓ Stopped Cart Service${NC}" || echo -e "${YELLOW}  Cart Service not running${NC}"
pkill -f shippingservice 2>/dev/null && echo -e "${GREEN}✓ Stopped Shipping Service${NC}" || echo -e "${YELLOW}  Shipping Service not running${NC}"
pkill -f "node index.js" 2>/dev/null && echo -e "${GREEN}✓ Stopped Payment Service${NC}" || echo -e "${YELLOW}  Payment Service not running${NC}"
pkill -f email_server.py 2>/dev/null && echo -e "${GREEN}✓ Stopped Email Service${NC}" || echo -e "${YELLOW}  Email Service not running${NC}"
pkill -f recommendation_server.py 2>/dev/null && echo -e "${GREEN}✓ Stopped Recommendation Service${NC}" || echo -e "${YELLOW}  Recommendation Service not running${NC}"
pkill -f checkoutservice 2>/dev/null && echo -e "${GREEN}✓ Stopped Checkout Service${NC}" || echo -e "${YELLOW}  Checkout Service not running${NC}"
pkill -f "frontend" 2>/dev/null && echo -e "${GREEN}✓ Stopped Frontend${NC}" || echo -e "${YELLOW}  Frontend not running${NC}"

echo -e "\n${GREEN}All services stopped!${NC}"
