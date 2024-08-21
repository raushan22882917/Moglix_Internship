function processImage() {
    var input = document.getElementById('imageInput');
    var file = input.files[0];

    if (file) {
        var reader = new FileReader();

        reader.onload = function(e) {
            var img = new Image();
            img.onload = function() {
                var canvas = document.createElement('canvas');
                var ctx = canvas.getContext('2d');
                canvas.width = img.width;
                canvas.height = img.height;
                ctx.drawImage(img, 0, 0);
                
                // Convert canvas to base64 image data
                var imageData = canvas.toDataURL();

                // Send image data to Flask backend for processing
                fetch('/remove-text', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({ image: imageData })
                })
                .then(response => response.json())
                .then(data => {
                    // Display processed image
                    document.getElementById('output').innerHTML = `<img src="${data.result}" alt="Processed Image">`;
                    document.getElementById('downloadButton').style.display = 'inline';
                    document.getElementById('downloadButton').setAttribute('data-image', data.result);
                })
                .catch(error => console.error('Error:', error));
            };
            img.src = e.target.result;
        };

        reader.readAsDataURL(file);
    }
}

function downloadImage() {
    var processedImage = document.getElementById('downloadButton').getAttribute('data-image');

    fetch('/download', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ image: processedImage })
    })
    .then(response => response.blob())
    .then(blob => {
        var url = window.URL.createObjectURL(blob);
        var a = document.createElement('a');
        a.href = url;
        a.download = 'processed_image.jpg';
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
    })
    .catch(error => console.error('Error:', error));
}
