# ── LocalStack ───────────────────────────────────────────────────────────────
variable "use_localstack" {
  description = "Si es true, apunta todos los endpoints al contenedor LocalStack local en lugar de AWS real."
  type        = bool
  default     = false
}

# ── General ──────────────────────────────────────────────────────────────────
variable "project_name" {
  description = "Nombre del proyecto, usado como prefijo en los recursos."
  type        = string
  default     = "reto-nequi"
}

variable "environment" {
  description = "Entorno de despliegue (dev, staging, prod)."
  type        = string
  default     = "dev"

  validation {
    condition     = contains(["dev", "staging", "prod"], var.environment)
    error_message = "El valor de environment debe ser dev, staging o prod."
  }
}

# ── AWS ──────────────────────────────────────────────────────────────────────
variable "aws_region" {
  description = "Región de AWS donde se desplegará la infraestructura."
  type        = string
  default     = "us-east-1"
}

# ── Red ──────────────────────────────────────────────────────────────────────
variable "vpc_cidr" {
  description = "Bloque CIDR para la VPC del backend."
  type        = string
  default     = "10.1.0.0/16"
}

variable "public_subnet_cidr" {
  description = "Bloque CIDR para la subnet pública del backend."
  type        = string
  default     = "10.1.1.0/24"
}

variable "availability_zone" {
  description = "AZ donde se creará la subnet pública."
  type        = string
  default     = "us-east-1a"
}

# ── EC2 ──────────────────────────────────────────────────────────────────────
variable "instance_type" {
  description = "Tipo de instancia EC2."
  type        = string
  default     = "t3.small"
}

variable "key_pair_name" {
  description = "Nombre del Key Pair de AWS para acceso SSH. Debe existir en la región."
  type        = string
}

variable "ami_id" {
  description = "ID de la AMI (Ubuntu 24.04 LTS). Déjalo vacío para resolución automática."
  type        = string
  default     = ""
}

variable "root_volume_size_gb" {
  description = "Tamaño del volumen raíz en GB."
  type        = number
  default     = 20
}

# ── Aplicación ───────────────────────────────────────────────────────────────
variable "repo_url" {
  description = "URL del repositorio Git."
  type        = string
  default     = "https://github.com/Jesus-Rojas/reto-nequi"
}

variable "app_api_key" {
  description = "API Key del backend."
  type        = string
  sensitive   = true
  default     = "nequi-secret-key-change-in-production"
}

variable "rate_limit_per_minute" {
  description = "Límite de peticiones por minuto."
  type        = number
  default     = 60
}

# ── SSH ──────────────────────────────────────────────────────────────────────
variable "allowed_ssh_cidrs" {
  description = "CIDRs permitidos para SSH. Restringe a tu IP en producción."
  type        = list(string)
  default     = ["0.0.0.0/0"]
}
