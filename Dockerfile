# Use the official Elixir image as the base
FROM elixir:latest

# Install Node.js and other dependencies
RUN apt-get update && \
    apt-get install -y nodejs npm postgresql-client && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

# Set the working directory
WORKDIR /app

# Copy the application files
COPY . /app

# Install Elixir dependencies
RUN mix local.hex --force && \
    mix local.rebar --force && \
    mix deps.get && \
    mix deps.compile

# Compile assets (if applicable)
RUN npm install --prefix ./assets && \
    npm run deploy --prefix ./assets && \
    mix phx.digest

# Expose the Phoenix port
EXPOSE 4000

# Start the Phoenix server
CMD ["mix", "phx.server"]