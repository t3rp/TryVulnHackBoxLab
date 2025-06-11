// Download PNG
function downloadImage(blob, pageNum) {
  const a = document.createElement('a');
  const imageUrl = URL.createObjectURL(blob);
  a.href = imageUrl;
  a.download = `${pageNum}.png`;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
}

// Get page
// 1 == hailstorm
// 2 == cyclone
// 3 == blizzard
async function fetchAndDownloadPage(pageNum) {
  const pageUrl = `https://enterprise.hackthebox.com/api/v1/cloud-labs/1/writeup?page=${pageNum}`;

  try {
    const response = await fetch(pageUrl, {
      method: 'GET',
      credentials: 'same-origin'
    });

    const blob = await response.blob();
    downloadImage(blob, pageNum);
  } catch (error) {
    console.error(`Error downloading the image from page ${pageNum}:`, error);
  }
}

// Delay
function delay(ms) {
  return new Promise(resolve => setTimeout(resolve, ms));
}

// Downloader
async function downloadImagesWithDelay() {
  for (let i = 1; i <= 116; i++) {
    await fetchAndDownloadPage(i);
    console.log(`Downloaded page ${i}`);
    if (i < 118) {
      await delay(5000);
    }
  }
}

// Do it
downloadImagesWithDelay();