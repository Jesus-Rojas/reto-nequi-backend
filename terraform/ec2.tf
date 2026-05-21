# ── AMI: Ubuntu 24.04 LTS ─────────────────────────────────────────────────────
# En LocalStack no existen AMIs reales, se omite la consulta con count = 0
data "aws_ami" "ubuntu" {
  count       = var.use_localstack ? 0 : 1
  most_recent = true
  owners      = ["099720109477"] # Canonical

  filter {
    name   = "name"
    values = ["ubuntu/images/hvm-ssd-gp3/ubuntu-noble-24.04-amd64-server-*"]
  }

  filter {
    name   = "virtualization-type"
    values = ["hvm"]
  }
}

locals {
  ami_id = var.ami_id != "" ? var.ami_id : (
    var.use_localstack ? "ami-12345678" : data.aws_ami.ubuntu[0].id
  )

  user_data = var.use_localstack ? null : templatefile("${path.module}/scripts/bootstrap.sh", {
    repo_url              = var.repo_url
    app_api_key           = var.app_api_key
    rate_limit_per_minute = var.rate_limit_per_minute
  })
}

# ── Instancia EC2 ─────────────────────────────────────────────────────────────
resource "aws_instance" "backend" {
  ami                    = local.ami_id
  instance_type          = var.instance_type
  subnet_id              = aws_subnet.public.id
  vpc_security_group_ids = [aws_security_group.backend.id]
  key_name               = var.use_localstack ? null : var.key_pair_name

  user_data                   = local.user_data
  user_data_replace_on_change = true

  # LocalStack no soporta root_block_device con gp3/encrypted
  dynamic "root_block_device" {
    for_each = var.use_localstack ? [] : [1]
    content {
      volume_type           = "gp3"
      volume_size           = var.root_volume_size_gb
      delete_on_termination = true
      encrypted             = true
    }
  }

  depends_on = [
    aws_subnet.public,
    aws_security_group.backend,
    aws_internet_gateway.backend,
  ]

  tags = {
    Name = "${var.project_name}-${var.environment}-backend"
  }
}

# ── Elastic IP ────────────────────────────────────────────────────────────────
resource "aws_eip" "backend" {
  instance = aws_instance.backend.id
  domain   = "vpc"

  tags = {
    Name = "${var.project_name}-${var.environment}-backend-eip"
  }

  depends_on = [aws_internet_gateway.backend]
}
