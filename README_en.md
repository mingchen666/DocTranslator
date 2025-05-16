# 📄 DocTranslator - Document AI Translation Tool 🚀

**DocTranslator** is a powerful document AI translation tool that supports translation of multiple file formats, is compatible with OpenAI format APIs, and supports batch operations and multi-threading. Whether you're an individual user or a corporate team, DocTranslator can help you efficiently complete document translation tasks! ✨

---

[[中文]](README.md)

---

## 🌟 Features

- **Supports Multiple Document Formats**  
  📑 **txt**, 📝 **markdown**, 📄 **word**, 📊 **csv**, 📈 **excel**, 📑 **pdf(Non scanned version)**, 📽️ **ppt** AI translation.
  


- **Compatible with OpenAI Format APIs**  
  🤖 Supports any endpoint API (proxy API) that conforms to the OpenAI format, flexibly adapting to various AI models.

- **Batch Operations**  
  🚀 Supports batch upload and translation of documents, improving work efficiency.

- **Multi-threading Support**  
  ⚡ Utilizes multi-threading technology to accelerate document translation.

- **Docker Deployment**  
  🐳 Supports one-click Docker deployment for simplicity and ease of use.

---

## 🛠️ Tech Stack

- **Frontend**: Vue 3 + Vite  
- **Backend**: Python + Flask + MySQL/SQLite  
- **AI Translation**: Compatible with OpenAI format APIs  
- **Deployment**: Docker + Nginx  

---

## Demo Preview  
### Frontend Demo  
![Frontend Page](docs/images/image1.png)  
![Frontend Page 2](docs/images/image2.png)  

### Backend Demo  
![Backend Page](docs/images/image3.png)  
![Backend Page 2](docs/images/image4.png)




## 🚀 Local Development

### 1. Clone the Project

```bash
git clone https://github.com/mingchen666/DocTranslator.git
cd DocTranslator
```

### 2. Configure Environment Variables

Fill in the necessary environment variables in the `backend/.env` file.

### 3. Start the Backend

Navigate to the backend directory and install dependencies:

```bash
cd backend
pip install -r requirements.txt
```

### 4. Run the Backend

```bash
python app.py
```

### 5. Start the Frontend and Admin Panel
> **The /dist folder is already built and ready for deployment. If not developing locally, you can skip the following steps.**

*Frontend*

```bash
cd frontend
pnpm install
pnpm dev
```

*Admin Panel*

```bash
cd admin
pnpm install
pnpm dev
```

### 6. Access the Project

- **Frontend**: http://localhost:1475  
- **Admin Panel**: http://localhost:8081  
- **Backend API**: http://localhost:5000  

---

## 🐳 Docker Deployment

### 1. Project Structure

```plaintext
DocTranslator/
├── frontend/          # Frontend code
├── admin/             # Admin panel code
├── backend/           # Backend code
├── nginx/             # Nginx configuration
│   └── nginx.conf     # Nginx configuration file
```

### 2. Create Docker Network

```bash
docker network create my-network
```

### 3. Backend Deployment

#### 3.1 Configure Environment Variables

Ensure the `DocTranslator/backend/.env` file is correctly filled with environment variables.

#### 3.2 Build Backend Image

```bash
cd DocTranslator/backend
docker build -t ezwork-api .
```

#### 3.3 Run Backend Container

```bash
cd ..
docker run -d \
  --name backend-container \
  --network my-network \
  -p 5000:5000 \
  -v $(pwd)/backend/db:/app/db \
  ezwork-api
```

### 4. Start Nginx

```bash
docker run -d \
  --name nginx-container \
  -p 1475:80 \
  -p 8081:8081 \
  -v $(pwd)/nginx/nginx.conf:/etc/nginx/conf.d/default.conf \
  -v $(pwd)/frontend/dist:/usr/share/nginx/html/frontend \
  -v $(pwd)/admin/dist:/usr/share/nginx/html/admin \
  --network my-network \
  nginx:stable-alpine
```

### 5. Access Services

- **Frontend**: http://localhost:1475  
- **Admin Panel**: http://localhost:8081  
- **Backend API**: http://localhost:5000  
   - *Account*: admin ;*Password*: 123456
---

## 💖 Support

If DocTranslator has been helpful to you, consider supporting the project! Your support keeps me motivated to continue developing! 😊  
🎉 **Support Code**:   
<img src="docs/e652698b250efb6e5151b084bd08814.jpg" alt="Support Code" width="300">
---

## 📢 Join Our Community  
If you have any questions or would like to discuss, feel free to join our QQ group!  
![QQ Group](docs/images/qq-group.png)


## 📝 User Guide

1. **Upload Documents**: Select the documents you want to translate on the frontend page and upload them.
2. **Select Translation Language**: Set the target language and start the translation.
3. **View Results**: Download the translated documents once the translation is complete.

---

## 🤝 Contribution Guide

We welcome contributions!

---

## 📜 License

[Apache-2.0 license](LICENSE).

---



## 📞 Contact Me

For any questions or suggestions, feel free to reach out:  

---

## 📌 Note

This project is a refactored and optimized version based on [ezwork](https://github.com/EHEWON/ezwork-ai-doc-translation). Thanks to the original author for their contribution! 🙏

## 🙏 Thanks

  [BabelDOC](https://github.com/funstory-ai/BabelDOC)


[![Star History](https://api.star-history.com/svg?repos=mingchen666/DocTranslator&type=Date)](https://star-history.com/#mingchen666/DocTranslator)