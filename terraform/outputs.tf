output "instance_id" {
  description = "ID de la instancia EC2 del backend."
  value       = aws_instance.backend.id
}

output "public_ip" {
  description = "Elastic IP pública del backend (en LocalStack es una IP emulada, no accesible)."
  value       = aws_eip.backend.public_ip
}

output "public_dns" {
  description = "DNS público de la Elastic IP del backend."
  value       = aws_eip.backend.public_dns
}

output "api_url" {
  description = "URL de la API FastAPI."
  value = var.use_localstack ? (
    "http://localhost:8000  ⚠ EC2 es emulado en LocalStack — usa: docker compose up --build"
  ) : (
    "http://${aws_eip.backend.public_ip}:8000"
  )
}

output "swagger_url" {
  description = "URL de la documentación Swagger."
  value = var.use_localstack ? (
    "http://localhost:8000/docs  ⚠ EC2 es emulado en LocalStack — usa: docker compose up --build"
  ) : (
    "http://${aws_eip.backend.public_ip}:8000/docs"
  )
}

output "health_url" {
  description = "Endpoint de health check del backend."
  value = var.use_localstack ? (
    "http://localhost:8000/health  ⚠ EC2 es emulado en LocalStack — usa: docker compose up --build"
  ) : (
    "http://${aws_eip.backend.public_ip}:8000/health"
  )
}

output "ssh_command" {
  description = "Comando SSH para conectarte a la instancia (solo AWS real)."
  value       = var.use_localstack ? "N/A — SSH no aplica en LocalStack" : "ssh -i <tu-key.pem> ubuntu@${aws_eip.backend.public_ip}"
}

output "vpc_id" {
  description = "ID de la VPC del backend."
  value       = aws_vpc.backend.id
}
