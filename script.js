"use strict";
let isProgramRunning = false; // Biến trạng thái để kiểm soát chương trình
function generateFields() {
  const numStages = parseInt(document.getElementById("num_stages").value);
  const container = document.getElementById("stages_container");
  const namefileheder = document.getElementById("file-name-header");
  namefileheder.innerHTML = "";
  container.innerHTML = "";
  if (isNaN(numStages) || numStages <= 0) {
    alert("Số giai đoạn phải lớn hơn 0!");
    return;
  }
  for (let i = 0; i < numStages; i++) {
    const div = document.createElement("div");
    div.className = "stage-row";
    div.innerHTML = `
            <span>Giai đoạn ${i + 1}</span>
            <input type="number" placeholder="Nhiệt độ (°C)" class="temperature">
            <input type="number" placeholder="Thời gian (phút)" class="time">
        `;
    container.appendChild(div);
  }
}
function showMessage(message, type) {
  const messageBox = document.getElementById("message-box");
  messageBox.textContent = message;
  messageBox.className = `message ${type}`; // Thêm class dựa trên loại thông báo
  messageBox.style.display = "block";
  // Ẩn thông báo sau 5 giây
  setTimeout(() => {
    messageBox.style.display = "none";
  }, 5000);
}
// Hiển thị phần tử loading và nút dừng chương trình
function showLoading(times) {
  return new Promise((resolve) => {
    const loading = document.getElementById("loading");
    loading.style.display = "flex"; // Hiển thị phần tử loading
    const stopButton = document.getElementById("stop-button");
    stopButton.style.display = "inline-block"; // Hiển thị nút dừng chương trình trong loading
    let countdownContainer = document.getElementById("countdown-container");
    if (!countdownContainer) {
      countdownContainer = document.createElement("div");
      countdownContainer.id = "countdown-container";
      loading.appendChild(countdownContainer);
    } else {
      countdownContainer.innerHTML = ""; // Xóa nội dung cũ nếu đã tồn tại
    }
    let currentStage = 0;
    let interval;
    function formatTime(seconds) {
      if (seconds >= 60) {
        const minutes = Math.floor(seconds / 60);
        const remainingSeconds = seconds % 60;
        return `${minutes}:${
          remainingSeconds < 10 ? "0" : ""
        }${remainingSeconds}`;
      } else {
        return `${seconds}`;
      }
    }
    function renderCountdown() {
      if (currentStage >= times.length) {
        loading.style.display = "none"; // Ẩn phần tử loading khi hoàn tất
        stopButton.style.display = "none"; // Ẩn nút dừng khi hoàn tất
        resolve(); // Hoàn tất Promise khi kết thúc đếm ngược
        return;
      }
      let timeRemaining = times[currentStage];
      countdownContainer.innerHTML = `<p>Giai đoạn ${
        currentStage + 1
      } - Đếm ngược: <span id="countdown">${formatTime(
        timeRemaining
      )}</span>s</p>`;
      interval = setInterval(() => {
        timeRemaining--;
        document.getElementById("countdown").textContent =
          formatTime(timeRemaining);
        if (timeRemaining <= 0) {
          clearInterval(interval);
          currentStage++;
          renderCountdown(); // Bắt đầu giai đoạn tiếp theo
        }
      }, 1000);
    }
    stopButton.addEventListener("click", () => {
      clearInterval(interval); // Dừng bộ đếm hiện tại
      loading.style.display = "none"; // Ẩn phần tử loading
      stopButton.style.display = "none"; // Ẩn nút dừng
      countdownContainer.innerHTML = ""; // Xóa nội dung đếm ngược
      resolve(); // Hoàn tất Promise khi dừng chương trình
    });
    renderCountdown(); // Bắt đầu đếm ngược cho giai đoạn đầu tiên
  });
}
// Ẩn phần tử loading
function hideLoading() {
  const loading = document.getElementById("loading");
  loading.style.display = "none"; // Ẩn phần tử loading
  const stopButton = document.getElementById("stop-button");
  stopButton.style.display = "none"; // Ẩn nút dừng chương trình khi không có loading
}
// Hàm lấy nhiệt độ từ Flask endpoint
function fetchTemperature() {
  fetch("/temperature")
    .then((response) => response.json())
    .then((data) => {
      document.getElementById("temperature").textContent =
        data.temperature.toFixed(2);
    })
    .catch((error) => {
      console.error("Lỗi:", error);
    });
}
setInterval(fetchTemperature, 1000);
// Hàm lưu dữ liệu
async function saveData() {
  const temperatures = [...document.querySelectorAll(".temperature")].map(
    (input) => parseFloat(input.value)
  );
  const times = [...document.querySelectorAll(".time")].map(
    (input) => parseInt(input.value) * 60
  );
  const fileName = document.getElementById("file_name_save").value;
  // Kiểm tra xem có giá trị NaN trong temperatures hoặc times không
  // Kiểm tra nếu tên tệp để trống
  if (!fileName) {
    alert("Tên tệp không được để trống. Vui lòng nhập tên tệp!");
    return;
  }
  if (temperatures.some(isNaN) || times.some(isNaN)) {
    alert("Vui lòng điền đầy đủ thông tin!");
    return;
  }
  const stages = temperatures.map((temp, index) => ({
    stage: index + 1,
    temperature: temp,
    time: times[index],
  }));
  const response = await fetch("/save", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ file_name: fileName, stages: stages }),
  });
  const result = await response.json();
  if (result.message) {
    showMessage(result.message, "success");
  } else {
    showMessage(result.error || "Đã xảy ra lỗi khi lưu dữ liệu.", "error");
  }
}
// Hàm chạy chương trình chính
async function runProgram() {
  const numStages = parseInt(document.getElementById("num_stages").value);
  if (isNaN(numStages) || numStages <= 0) {
    alert("Số giai đoạn phải lớn hơn 0!");
    return;
  }
  const temperatures = [...document.querySelectorAll(".temperature")].map(
    (input) => parseFloat(input.value)
  );
  const times = [...document.querySelectorAll(".time")].map(
    (input) => parseInt(input.value) * 60
  );
  if (temperatures.includes(NaN) || times.includes(NaN)) {
    alert("Vui lòng điền đầy đủ thông tin!");
    return;
  }
  const stages = temperatures.map((temp, index) => ({
    stage: index + 1,
    temperature: temp,
    time: times[index],
  }));
  isProgramRunning = true;
  await Promise.all([
    showLoading(times),
    fetch("/run", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ stages: stages }),
    }),
  ]);
  hideLoading();
  alert("Hoàn Thành!");
}
// Hàm tải danh sách công thức từ server
async function loadRecipes() {
  await fetch("/list_recipes")
    .then((response) => response.json())
    .then((data) => {
      const recipesList = document.getElementById("recipes-list");
      recipesList.innerHTML = ""; // Xóa danh sách cũ
      // Hiển thị danh sách các công thức
      data.recipes.forEach((recipe) => {
        const li = document.createElement("li");
        li.textContent = recipe;
        recipesList.appendChild(li);
      });
    })
    .catch((error) => console.error("Lỗi khi tải danh sách công thức:", error));
}
// Hàm để lấy tên tệp từ input và gửi yêu cầu đến server
async function loadData() {
  const fileName = document.getElementById("file_name_export").value.trim();
  if (!fileName) {
    alert("Vui lòng nhập tên tệp.");
    return;
  }
  // Cập nhật tên tệp vào phần tử <h3>
  const namefileheder = document.getElementById("file-name-header");
  namefileheder.innerHTML = ""; // Xóa nội dung cũ
  namefileheder.innerHTML = `<h3>Tên công thức: ${fileName}</h3>
    `;
  // Lấy dữ liệu giai đoạn từ server
  await fetch("/export_data", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ file_name: fileName }),
  })
    .then((response) => response.json())
    .then((data) => {
      if (data.error) {
        alert(data.error);
        return;
      }
      displayStagesInputs(data.stages);
    })
    .catch((error) => console.error("Lỗi:", error));
}
// Hàm render hiển thị giai đoạn
function displayStagesInputs(stages) {
  const stagesContainer = document.getElementById("stages_container");
  stagesContainer.innerHTML = "";
  // Cập nhật số giai đoạn vào input num_stages
  const numStagesInput = document.getElementById("num_stages");
  numStagesInput.value = stages.length;
  stages.forEach((stage, index) => {
    const div = document.createElement("div");
    div.className = "stage-row";
    div.innerHTML = `
      <span>Giai đoạn ${index + 1}</span>
      <input type="number" value="${
        stage.temperature
      }" placeholder="Nhiệt độ (°C)" class="temperature">
      <input type="number" value="${(stage.time / 60).toFixed(
        2
      )}" placeholder="Thời gian (phút)" class="time">
    `;
    stagesContainer.appendChild(div);
  });
}
// Hàm dừng chương trình
async function stopProgram() {
  isProgramRunning = false;
  hideLoading();
  await fetch("/stop", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
  })
    .then((response) => response.json())
    .then((data) => {
      if (data.message) {
        showMessage(data.message, "success");
      } else if (data.error) {
        showMessage(data.error, "error");
      }
    })
    .catch((error) => {
      console.error("Lỗi khi dừng chương trình:", error);
      showMessage("Lỗi khi dừng chương trình.", "error");
    });
}
