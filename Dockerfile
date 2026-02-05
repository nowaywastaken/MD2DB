# Multi-stage Dockerfile for MD2DB Rust Application
# Supports ARM64 and AMD64 architectures

# Stage 1: Build stage
FROM rust:1.75-slim-bookworm AS builder

# Install build dependencies
RUN apt-get update && apt-get install -y \
    pkg-config \
    libssl-dev \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /usr/src/md2db

# Copy Cargo manifests first for caching
COPY Cargo.toml Cargo.lock ./

# Create a dummy main.rs to build dependencies
RUN mkdir src && \
    echo "fn main() {}" > src/main.rs && \
    echo "pub fn main() {}" > src/lib.rs

# Build dependencies (this layer will be cached)
RUN cargo build --release && \
    rm -rf src

# Copy actual source code
COPY src ./src

# Build the application
RUN cargo build --release

# Stage 2: Runtime stage (minimal image)
FROM debian:bookworm-slim

# Install runtime dependencies only
RUN apt-get update && apt-get install -y \
    ca-certificates \
    libssl3 \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user for security
RUN groupadd -r md2db && useradd -r -g md2db md2db

# Set working directory
WORKDIR /app

# Copy the binary from builder
COPY --from=builder /usr/src/md2db/target/release/md2db /app/md2db

# Change ownership to non-root user
RUN chown -R md2db:md2db /app

# Switch to non-root user
USER md2db

# Environment variables
ENV RUST_LOG=info \
    PORT=8080 \
    HOST=0.0.0.0

# Expose port
EXPOSE 8080

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8080/health || exit 1

# Run the application
CMD ["./md2db"]
