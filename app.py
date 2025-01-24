from flask import Flask, render_template, request, jsonify
import tensorflow as tf
import numpy as np
from PIL import Image
import io
import base64

app = Flask(__name__)

# Load AI Model
MODEL_PATH = "petvision_model.tflite"
interpreter = tf.lite.Interpreter(model_path=MODEL_PATH)
interpreter.allocate_tensors()

# Get Input & Output Tensors
input_details = interpreter.get_input_details()
output_details = interpreter.get_output_details()

# Define Class Labels
CLASS_LABELS = [
    "Cataract", "Cherry Eye", "Conjunctivitis", "Deep Corneal Ulcer",
    "Ectropion", "Entropion", "Glaucoma", "KCS (Dry Eye)", "Normal Eye", "Superficial Corneal Ulcer"
]

# Advice Dictionary
ADVICE_INFO = {
    "Superficial Corneal Ulcer": """📌 สาเหตุ: อาจเกิดจากบาดเจ็บ, สิ่งแปลกปลอม, หรือการติดเชื้อ
                                    📌 การรักษา:
                                    ยาหยอดตาปฏิชีวนะและต้านการอักเสบ 🧴
                                    การใช้ E-collar (ปลอกคอกันเลีย) 🦺
                                    การรักษาทางศัลยกรรม (ในกรณีแผลลึก) 🔬
                                    📌 ค่าใช้จ่ายเบื้องต้น: 1,000 - 3,500 บาท""",
    "Conjunctivitis": """📌 สาเหตุ: เกิดจากการระคายเคือง เช่น ฝุ่น, ควัน, การติดเชื้อ
                        📌 การรักษา:
                        ยาหยอดตาปฏิชีวนะ 💧
                        การใช้ผ้าอุ่นประคบช่วยลดอาการบวม 🤕
                        หลีกเลี่ยงฝุ่นละอองหรือสารเคมีที่ก่อให้เกิดการระคายเคือง 🚫
                        📌 ค่าใช้จ่ายเบื้องต้น: 500 - 2,500 บาท""",
    "Cataract": """📌 สาเหตุ: พันธุกรรม, การกระทบกระเทือน, โรคเบาหวาน
                📌 การรักษา:
                    หยอดยาขยายม่านตาและป้องกันการอักเสบ 💊
                    การผ่าตัดเปลี่ยนเลนส์ตา เป็นทางเลือกที่ดีที่สุด 🏥
                📌 ค่าใช้จ่ายเบื้องต้น: 20,000 - 50,000 บาท (ขึ้นอยู่กับวิธีการรักษาและโรงพยาบาลสัตว์)""",
    "KCS (Dry Eye)": """📌 สาเหตุ: การผลิตน้ำตาลดลง, การติดเชื้อเรื้อรัง
                        📌 การรักษา:
                            หยอดยากระตุ้นการผลิตน้ำตา 💧
                            ใช้สารหล่อลื่นตาเพื่อป้องกันการอักเสบ 🛡️
                            ในกรณีรุนแรง อาจต้องผ่าตัดเปลี่ยนท่อน้ำตา 🏥
                        📌 ค่าใช้จ่ายเบื้องต้น: 800 - 5,000 บาท""",
    "Glaucoma": """📌 สาเหตุ: ความดันลูกตาสูง, การอักเสบของตาภายใน
                📌 การรักษา:
                    หยอดยาเพื่อลดความดันตา 💊
                    กรณีรุนแรง อาจต้อง ผ่าตัดกำจัดตาออก (Enucleation) 😞
                📌 ค่าใช้จ่ายเบื้องต้น: 2,500 - 15,000 บาท (หากต้องผ่าตัดอาจสูงถึง 25,000 บาท)""",
    "Ectropion": """📌 สาเหตุ: พันธุกรรม, ความผิดปกติของกล้ามเนื้อตา
                    📌 การรักษา:
                        หยอดยาปฏิชีวนะและต้านอักเสบ 🧴
                        ในกรณีรุนแรง อาจต้องทำศัลยกรรมแก้ไขหนังตา ✂️
                    📌 ค่าใช้จ่ายเบื้องต้น: 1,500 - 10,000 บาท""",
    "Entropion": """📌 สาเหตุ: หนังตาหรือขนม้วนเข้าไปในตา ทำให้เกิดการระคายเคือง
                    📌 การรักษา:
                        ใช้ยาหยอดตาลดการอักเสบ 💧
                        ในกรณีรุนแรง อาจต้อง ทำศัลยกรรมผ่าตัดแก้ไขหนังตา 🏥
                    📌 ค่าใช้จ่ายเบื้องต้น: 5,000 - 20,000 บาท (หากต้องผ่าตัด)""",
    "Cherry Eye": """📌 สาเหตุ: ต่อมใต้หนังตาชั้นที่สามอักเสบและปลิ้นออกมา
                        📌 การรักษา:
                            ใช้ยาหยอดตาลดอาการอักเสบ 💊
                            หากเป็นถาวร อาจต้อง ผ่าตัดเย็บต่อมหนังตา ✂️
                        📌 ค่าใช้จ่ายเบื้องต้น: 3,500 - 12,000 บาท (หากต้องผ่าตัด)""",
    "Deep Corneal Ulcer": """📌 สาเหตุ: เกิดจากการติดเชื้อหรือบาดเจ็บรุนแรง
                            📌 การรักษา:
                                ใช้ยาหยอดตาปฏิชีวนะและต้านการอักเสบ 💧
                                อาจต้อง เย็บหนังตาชั้นที่สาม เพื่อช่วยให้แผลสมานเร็วขึ้น 🏥
                            📌 ค่าใช้จ่ายเบื้องต้น: 2,500 - 10,000 บาท""",
    "Normal Eye": """📌 ไม่มีอาการผิดปกติ
                    📌 การดูแลสุขภาพตาเบื้องต้น:
                        เช็ดทำความสะอาดตาด้วยน้ำเกลือ 📌
                        หลีกเลี่ยงการให้สัตว์เลี้ยงอยู่ในที่มีฝุ่นหรือสารเคมี 🚫"""
}

# Function to preprocess image
def preprocess_image(image):
    image = image.convert("RGB").resize((224, 224))  # Ensure RGB format & Resize
    image = np.array(image) / 255.0   # Normalize
    image = np.expand_dims(image, axis=0).astype(np.float32)  # Add batch dimension
    return image

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/predict', methods=['POST'])
def predict():
    try:
        if 'file' in request.files:
            file = request.files['file']
            image = Image.open(io.BytesIO(file.read()))
        elif 'image' in request.json:
            image_data = request.json['image']
            image = Image.open(io.BytesIO(base64.b64decode(image_data.split(',')[1])))
        else:
            return jsonify({"error": "No image provided"}), 400

        processed_image = preprocess_image(image)

        # Run model inference
        interpreter.set_tensor(input_details[0]['index'], processed_image)
        interpreter.invoke()
        output_data = interpreter.get_tensor(output_details[0]['index'])

        # Get Top 3 Predictions
        top_indices = np.argsort(output_data[0])[::-1][:3]
        top_predictions = [{"label": CLASS_LABELS[i], "confidence": round(float(output_data[0][i]) * 100, 2), "advice": ADVICE_INFO[CLASS_LABELS[i]]} for i in top_indices]

        return jsonify({"predictions": top_predictions})

    except Exception as e:
        return jsonify({"error": f"Error processing image: {str(e)}"}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)

