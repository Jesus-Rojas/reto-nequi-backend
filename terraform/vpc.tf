# ── VPC ──────────────────────────────────────────────────────────────────────
resource "aws_vpc" "backend" {
  cidr_block           = var.vpc_cidr
  enable_dns_hostnames = true
  enable_dns_support   = true

  tags = {
    Name = "${var.project_name}-${var.environment}-backend-vpc"
  }
}

# ── Internet Gateway ─────────────────────────────────────────────────────────
resource "aws_internet_gateway" "backend" {
  vpc_id = aws_vpc.backend.id

  tags = {
    Name = "${var.project_name}-${var.environment}-backend-igw"
  }
}

# ── Subnet pública ───────────────────────────────────────────────────────────
resource "aws_subnet" "public" {
  vpc_id                  = aws_vpc.backend.id
  cidr_block              = var.public_subnet_cidr
  availability_zone       = var.availability_zone
  map_public_ip_on_launch = true

  tags = {
    Name = "${var.project_name}-${var.environment}-backend-public-subnet"
  }
}

# ── Tabla de rutas pública ───────────────────────────────────────────────────
resource "aws_route_table" "public" {
  vpc_id = aws_vpc.backend.id

  route {
    cidr_block = "0.0.0.0/0"
    gateway_id = aws_internet_gateway.backend.id
  }

  tags = {
    Name = "${var.project_name}-${var.environment}-backend-public-rt"
  }
}

resource "aws_route_table_association" "public" {
  subnet_id      = aws_subnet.public.id
  route_table_id = aws_route_table.public.id
}
