FROM eclipse-temurin:17-jdk-alpine
WORKDIR /app

# Download Lavalink jar (replace version if needed)
RUN wget https://github.com/freyacodes/Lavalink/releases/download/4.0.4/Lavalink.jar -O lavalink.jar

COPY application.yml ./
COPY plugins ./plugins

EXPOSE 8080
CMD ["java", "-jar", "lavalink.jar"]
