let capturedImageData = null;

document.getElementById('fileInput').addEventListener('change', function(event) {
    let file = event.target.files[0];
    if (file) {
        let reader = new FileReader();
        reader.onload = function(e) {
            document.getElementById('uploadedImage').src = e.target.result;
            document.getElementById('uploadedImage').style.display = 'block';
            capturedImageData = null;
        };
        reader.readAsDataURL(file);
    }
});

let cameraStream;
document.getElementById('openCameraBtn').addEventListener('click', function() {
    document.getElementById('cameraContainer').style.display = 'block';
    navigator.mediaDevices.getUserMedia({ video: true })
        .then(stream => {
            cameraStream = stream;
            document.getElementById('camera').srcObject = stream;
        })
        .catch(err => alert('Camera access denied!'));
});

document.getElementById('captureBtn').addEventListener('click', function() {
    let video = document.getElementById('camera');
    let canvas = document.createElement('canvas');
    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;
    let ctx = canvas.getContext('2d');
    ctx.drawImage(video, 0, 0, canvas.width, canvas.height);

    capturedImageData = canvas.toDataURL();
    document.getElementById('uploadedImage').src = capturedImageData;
    document.getElementById('uploadedImage').style.display = 'block';
});

document.getElementById('closeCameraBtn').addEventListener('click', function() {
    document.getElementById('cameraContainer').style.display = 'none';
    if (cameraStream) {
        cameraStream.getTracks().forEach(track => track.stop());
    }
});

document.getElementById('predictBtn').addEventListener('click', function() {
    let fileInput = document.getElementById('fileInput').files[0];

    if (!fileInput && !capturedImageData) {
        alert("Please upload an image or capture one first!");
        return;
    }

    document.getElementById('processing').style.display = 'block';

    let fetchOptions;
    if (capturedImageData) {
        fetchOptions = {
            method: 'POST',
            body: JSON.stringify({ "image": capturedImageData }),
            headers: { 'Content-Type': 'application/json' }
        };
    } else {
        let formData = new FormData();
        formData.append("file", fileInput);
        fetchOptions = { method: 'POST', body: formData };
    }

    fetch('/predict', fetchOptions)
        .then(response => response.json())
        .then(data => {
            if (data.error) {
                alert(data.error);
                return;
            }

            document.getElementById('prediction1').innerText = data.predictions[0].label + " (" + data.predictions[0].confidence + "%) - " + data.predictions[0].advice;
            document.getElementById('prediction2').innerText = data.predictions[1].label + " (" + data.predictions[1].confidence + "%) - " + data.predictions[1].advice;
            document.getElementById('prediction3').innerText = data.predictions[2].label + " (" + data.predictions[2].confidence + "%) - " + data.predictions[2].advice;

            document.getElementById('processing').style.display = 'none';
        })
        .catch(error => alert("Error processing image"));
});
