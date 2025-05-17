document.addEventListener('DOMContentLoaded', function () {
    const lightboxModalElement = document.getElementById('lightboxModal');
    if (lightboxModalElement) {
        const lightboxImage = document.getElementById('lightboxImage');
        const lightboxModalLabel = document.getElementById('lightboxModalLabel');
        const lightboxDownloadButton = document.getElementById('lightboxDownload');
        const lightboxCopyLinkButton = document.getElementById('lightboxCopyLink');

        let currentImageSrc = ''; // 用于复制链接

        lightboxModalElement.addEventListener('show.bs.modal', function (event) {
            // Button that triggered the modal
            const button = event.relatedTarget;
            // Extract info from data-bs-* attributes
            const imageSrc = button.getAttribute('data-lightbox-src');
            const imageAlt = button.getAttribute('data-lightbox-alt') || '图片预览';

            currentImageSrc = imageSrc; // 更新当前图片源

            if (lightboxImage) {
                lightboxImage.src = imageSrc;
                lightboxImage.alt = imageAlt;
            }
            if (lightboxModalLabel) {
                lightboxModalLabel.textContent = imageAlt; // 更新模态框标题
            }
            if (lightboxDownloadButton) {
                lightboxDownloadButton.href = imageSrc;
            }
        });

        if (lightboxCopyLinkButton) {
            lightboxCopyLinkButton.addEventListener('click', function() {
                if (currentImageSrc) {
                    navigator.clipboard.writeText(window.location.origin + currentImageSrc)
                        .then(() => {
                            // 可选：提供一个复制成功的提示
                            const originalText = lightboxCopyLinkButton.textContent;
                            lightboxCopyLinkButton.textContent = '已复制!';
                            setTimeout(() => {
                                lightboxCopyLinkButton.textContent = originalText;
                            }, 1500);
                        })
                        .catch(err => {
                            console.error('无法复制链接: ', err);
                            alert('复制链接失败，请手动复制。');
                        });
                }
            });
        }
    }
});