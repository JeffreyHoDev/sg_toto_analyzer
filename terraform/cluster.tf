# Create a cluster
resource "mongodbatlas_cluster" "sg_toto_analyzer" {
  project_id                  = var.mongodbatlas_project_id
  name                        = "SGTotoAnalyzerCluster"
  provider_name               = "TENANT" # Required for M0 and M2 clusters
  provider_instance_size_name = "M0"     # Specifies the free tier
  backing_provider_name       = "AWS"    # Choose the cloud provider (AWS, GCP, or AZURE)
  provider_region_name        = "AP_SOUTHEAST_1" # Choose an available region for M0 clusters
  auto_scaling_disk_gb_enabled = false
  mongo_db_major_version      = "6.0" # Specify the desired MongoDB version


  backup_enabled          = false
}

# Database user
resource "mongodbatlas_database_user" "mongodb_jeffrey" {
    project_id = var.mongodbatlas_project_id
    username = var.db_user_username
    password = var.db_user_password
    auth_database_name = "admin"

    roles {
        role_name = "readWrite"
        database_name = "admin"
    }

    roles {
        role_name     = "readWrite"
        database_name = "lottery_db" # Replace with your actual DB name
    }

    roles {
        role_name     = "atlasAdmin"
        database_name = "admin"
    }

}

# Output the connection string for easy access
output "connection_string_srv" {
  value = mongodbatlas_cluster.sg_toto_analyzer.srv_address
}