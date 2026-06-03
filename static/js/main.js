// 主JavaScript文件
// 可以在这里添加全局的JavaScript功能

// 示例：平滑滚动
document.querySelectorAll('a[href^="#"]').forEach(anchor => {
    anchor.addEventListener('click', function (e) {
        e.preventDefault();
        const target = document.querySelector(this.getAttribute('href'));
        if (target) {
            target.scrollIntoView({
                behavior: 'smooth',
                block: 'start'
            });
        }
    });
});

// 示例：表单验证增强
document.addEventListener('DOMContentLoaded', function() {
    // 为所有输入框添加实时验证
    const inputs = document.querySelectorAll('input, textarea, select');
    inputs.forEach(input => {
        input.addEventListener('blur', function() {
            validateInput(this);
        });
    });
});

function validateInput(input) {
    // 简单的验证逻辑
    if (input.required && !input.value.trim()) {
        input.classList.add('error');
    } else {
        input.classList.remove('error');
    }
}

// 反馈功能
let selectedImages = [];  // 存储选中的图片文件
let selectedArchives = []; // 存储选中的压缩包文件

// 打开反馈弹窗
function openFeedbackModal() {
    document.getElementById('feedbackModal').classList.add('active');
    loadProducts();
    document.body.style.overflow = 'hidden';
}

// 关闭反馈弹窗
function closeFeedbackModal() {
    document.getElementById('feedbackModal').classList.remove('active');
    document.body.style.overflow = '';
    resetFeedbackForm();
}

// 加载产品列表
function loadProducts() {
    fetch('/api/products')
        .then(response => response.json())
        .then(products => {
            const select = document.getElementById('productId');
            select.innerHTML = '<option value="">请选择产品</option>';
            products.forEach(product => {
                const option = document.createElement('option');
                option.value = product.id;
                option.textContent = product.name;
                option.dataset.realId = product.id; // 存储加密后的ID
                select.appendChild(option);
            });
        })
        .catch(error => {
            console.error('加载产品列表失败:', error);
            showToast('加载产品列表失败', 'error');
        });
}

// 处理图片选择
function handleImageSelect(event) {
    const files = Array.from(event.target.files);
    console.log('图片选择事件触发，文件数量:', files.length);
    const validTypes = ['image/png', 'image/jpeg', 'image/jpg', 'image/gif'];
    
    files.forEach(file => {
        console.log('处理文件:', file.name, '类型:', file.type);
        if (validTypes.includes(file.type)) {
            selectedImages.push(file);
            console.log('添加到图片列表，当前数量:', selectedImages.length);
        } else {
            showToast(`文件 ${file.name} 不是有效的图片格式`, 'error');
            console.warn('无效的图片类型:', file.type);
        }
    });
    
    console.log('更新文件预览，图片数:', selectedImages.length, '压缩包数:', selectedArchives.length);
    updateFilePreview();
}

// 处理压缩包选择
function handleArchiveSelect(event) {
    const files = Array.from(event.target.files);
    console.log('压缩包选择事件触发，文件数量:', files.length);
    const validTypes = ['application/zip', 'application/x-rar-compressed', 'application/x-7z-compressed', 'application/gzip'];
    const validExtensions = ['.zip', '.rar', '.7z', '.tar', '.gz'];
    
    files.forEach(file => {
        console.log('处理文件:', file.name, '类型:', file.type);
        const hasValidExt = validExtensions.some(ext => file.name.toLowerCase().endsWith(ext));
        if (hasValidExt || validTypes.includes(file.type)) {
            selectedArchives.push(file);
            console.log('添加到压缩包列表，当前数量:', selectedArchives.length);
        } else {
            showToast(`文件 ${file.name} 不是有效的压缩包格式`, 'error');
            console.warn('无效的压缩包类型:', file.type);
        }
    });
    
    console.log('更新文件预览，图片数:', selectedImages.length, '压缩包数:', selectedArchives.length);
    updateFilePreview();
}

// 更新文件预览
function updateFilePreview() {
    const previewDiv = document.getElementById('filePreview');
    const imageCount = selectedImages.length;
    const archiveCount = selectedArchives.length;
    const totalCount = imageCount + archiveCount;
    
    console.log('updateFilePreview 调用，总数:', totalCount);
    
    if (totalCount === 0) {
        previewDiv.innerHTML = '<p style="color: #999; font-size: 12px;">未选择文件</p>';
        previewDiv.classList.remove('show');
        console.log('无文件，显示默认提示');
        return;
    }
    
    // 显示预览区域
    previewDiv.classList.add('show');
    
    // 清空预览区域
    previewDiv.innerHTML = '';
    
    // 创建容器
    const container = document.createElement('div');
    container.style.cssText = 'display: flex; flex-wrap: wrap; gap: 8px; margin-bottom: 8px;';
    
    // 显示图片缩略图
    selectedImages.forEach((file, index) => {
        const reader = new FileReader();
        reader.onload = function(e) {
            const imgDiv = document.createElement('div');
            imgDiv.style.cssText = 'position: relative; display: inline-block;';
            imgDiv.innerHTML = `
                <img src="${e.target.result}" style="width: 60px; height: 60px; object-fit: cover; border-radius: 4px; border: 1px solid #ddd;">
                <span style="position: absolute; top: -5px; right: -5px; background: #ff4444; color: white; border-radius: 50%; width: 18px; height: 18px; font-size: 12px; line-height: 18px; text-align: center; cursor: pointer;" onclick="removeImage(${index})">×</span>
            `;
            container.appendChild(imgDiv);
            console.log('图片缩略图已添加:', file.name);
        };
        reader.readAsDataURL(file);
    });
    
    // 显示压缩包
    selectedArchives.forEach((file, index) => {
        const archiveDiv = document.createElement('div');
        archiveDiv.style.cssText = 'position: relative; display: inline-block;';
        
        // 先显示默认预览
        showDefaultArchivePreview(archiveDiv, file);
        
        // 如果是ZIP文件，尝试读取内容并更新预览
        if (file.name.toLowerCase().endsWith('.zip')) {
            readZipContents(file).then(contents => {
                // 更新预览显示文件数量
                const previewBox = archiveDiv.querySelector('div');
                if (previewBox) {
                    previewBox.innerHTML = `
                        <span style="font-size: 16px; line-height: 1;">📦</span>
                        <span style="font-size: 8px; color: #666; margin-top: 2px;">${contents.length} 个文件</span>
                    `;
                }
            }).catch(err => {
                // 读取失败保持默认预览
                console.log('ZIP解析失败:', file.name);
            });
        }
        
        // 添加删除按钮
        const deleteBtn = document.createElement('span');
        deleteBtn.style.cssText = 'position: absolute; top: -5px; right: -5px; background: #ff4444; color: white; border-radius: 50%; width: 18px; height: 18px; font-size: 12px; line-height: 18px; text-align: center; cursor: pointer; z-index: 1;';
        deleteBtn.textContent = '×';
        deleteBtn.onclick = function() { removeArchive(index); };
        archiveDiv.appendChild(deleteBtn);
        
        container.appendChild(archiveDiv);
        console.log('压缩包已添加:', file.name);
    });
    
    previewDiv.appendChild(container);
    
    // 添加统计信息
    const stats = document.createElement('p');
    stats.style.cssText = 'color: #666; font-size: 12px; margin-top: 8px;';
    stats.textContent = `已选择 ${imageCount} 张图片, ${archiveCount} 个压缩包`;
    previewDiv.appendChild(stats);
    
    console.log('文件预览HTML已更新');
}

// 移除图片
function removeImage(index) {
    selectedImages.splice(index, 1);
    updateFilePreview();
}

// 移除压缩包
function removeArchive(index) {
    selectedArchives.splice(index, 1);
    updateFilePreview();
}

// 显示默认压缩包预览
function showDefaultArchivePreview(container, file) {
    const defaultPreview = document.createElement('div');
    defaultPreview.style.cssText = 'width: 60px; height: 60px; background: #f0f0f0; border-radius: 4px; border: 1px solid #ddd; display: flex; flex-direction: column; align-items: center; justify-content: center; font-size: 10px; text-align: center; color: #666;';
    defaultPreview.innerHTML = `
        <span style="font-size: 20px; line-height: 1;">📦</span>
        <span style="font-size: 8px; color: #999; margin-top: 2px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; max-width: 56px;">${file.name.length > 8 ? file.name.substring(0, 8) + '...' : file.name}</span>
    `;
    container.innerHTML = '';
    container.appendChild(defaultPreview);
}

// 读取ZIP文件内容
async function readZipContents(zipFile) {
    return new Promise((resolve, reject) => {
        try {
            const reader = new FileReader();
            reader.onload = function(e) {
                try {
                    // 简单的ZIP文件解析（读取中央目录）
                    const data = new Uint8Array(e.target.result);
                    const files = [];
                    
                    // 从后向前搜索ZIP中央目录头（PK\x01\x02）
                    let pos = data.length - 22;
                    while (pos >= 0) {
                        if (data[pos] === 0x50 && data[pos+1] === 0x4b && 
                            data[pos+2] === 0x01 && data[pos+3] === 0x02) {
                            // 找到中央目录头
                            const filenameLength = data[pos+28] | (data[pos+29] << 8);
                            const filename = String.fromCharCode(...data.slice(pos+46, pos+46+filenameLength));
                            if (!filename.endsWith('/')) { // 跳过目录
                                files.push(filename);
                            }
                            pos -= 46 + filenameLength;
                        } else {
                            pos--;
                        }
                    }
                    
                    resolve(files.slice(0, 10)); // 最多显示10个文件
                } catch (parseError) {
                    reject(parseError);
                }
            };
            reader.onerror = () => reject(reader.error);
            reader.readAsArrayBuffer(zipFile);
        } catch (err) {
            reject(err);
        }
    });
}

// 重置表单
function resetFeedbackForm() {
    document.getElementById('feedbackForm').reset();
    selectedImages = [];
    selectedArchives = [];
    updateFilePreview();
}

// 提交反馈
function submitFeedback(event) {
    event.preventDefault();
    
    const productId = document.getElementById('productId').value;
    const description = document.getElementById('description').value;
    const contact = document.getElementById('contact').value;
    
    console.log('提交反馈，产品ID:', productId, '描述:', description);
    console.log('已选文件 - 图片:', selectedImages.length, '压缩包:', selectedArchives.length);
    
    if (!productId || !description) {
        showToast('请填写必填项', 'error');
        console.warn('验证失败：缺少必填项');
        return;
    }
    
    // 获取产品名称
    const productSelect = document.getElementById('productId');
    const productName = productSelect.options[productSelect.selectedIndex].text;
    
    // 构建FormData
    const formData = new FormData();
    formData.append('product_id', productId);
    formData.append('product_name', productName);
    formData.append('description', description);
    formData.append('contact', contact);
    
    // 添加多张图片
    selectedImages.forEach((file, index) => {
        formData.append('images', file);
        console.log('FormData添加图片:', file.name);
    });
    
    // 添加多个压缩包
    selectedArchives.forEach((file, index) => {
        formData.append('archives', file);
        console.log('FormData添加压缩包:', file.name);
    });
    
    console.log('FormData准备完成，开始提交...');
    
    // 禁用提交按钮
    const submitBtn = event.target.querySelector('.btn-primary') || document.querySelector('.modal-footer .btn-primary');
    submitBtn.disabled = true;
    submitBtn.textContent = '提交中...';
    
    fetch('/api/feedback', {
        method: 'POST',
        body: formData
    })
    .then(response => {
        console.log('服务器响应状态:', response.status);
        return response.json();
    })
    .then(data => {
        console.log('服务器响应数据:', data);
        if (data.success) {
            showToast(data.message || '反馈提交成功', 'success');
            // 显示已上传的文件信息
            if (selectedImages.length > 0 || selectedArchives.length > 0) {
                displayUploadedFiles(selectedImages, selectedArchives);
            }
            closeFeedbackModal();
        } else {
            showToast(data.error || '提交失败，请稍后重试', 'error');
            console.error('提交失败:', data.error);
        }
    })
    .catch(error => {
        console.error('提交反馈失败:', error);
        showToast('提交失败，请稍后重试', 'error');
    })
    .finally(() => {
        submitBtn.disabled = false;
        submitBtn.textContent = '提交反馈';
    });
}

// Toast通知
function showToast(message, type = 'success') {
    const container = document.getElementById('toastContainer');
    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;
    
    const icon = type === 'success' ? '✓' : '✗';
    toast.innerHTML = `
        <span class="toast-icon">${icon}</span>
        <span class="toast-message">${message}</span>
    `;
    
    container.appendChild(toast);
    
    // 5秒后自动消失
    setTimeout(() => {
        toast.classList.add('hiding');
        setTimeout(() => {
            if (toast.parentNode) {
                toast.parentNode.removeChild(toast);
            }
        }, 300);
    }, 5000);
}

// 点击弹窗外部关闭
document.addEventListener('click', function(event) {
    const modal = document.getElementById('feedbackModal');
    if (modal && event.target === modal) {
        closeFeedbackModal();
    }
});

// ESC键关闭弹窗
document.addEventListener('keydown', function(event) {
    if (event.key === 'Escape') {
        closeFeedbackModal();
    }
});

// 显示已上传的文件列表
function displayUploadedFiles(images, archives) {
    // 创建或获取上传历史容器
    let historyContainer = document.getElementById('uploadHistory');
    if (!historyContainer) {
        historyContainer = document.createElement('div');
        historyContainer.id = 'uploadHistory';
        historyContainer.style.cssText = 'position: fixed; bottom: 20px; right: 20px; width: 320px; max-height: 400px; overflow-y: auto; background: white; border: 1px solid #ddd; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); z-index: 1000; padding: 15px;';
        document.body.appendChild(historyContainer);
    }
    
    // 添加标题
    const title = document.createElement('div');
    title.style.cssText = 'font-weight: bold; margin-bottom: 10px; padding-bottom: 5px; border-bottom: 1px solid #eee; font-size: 14px;';
    title.textContent = '📤 最近上传';
    historyContainer.insertBefore(title, historyContainer.firstChild);
    
    // 添加时间戳
    const now = new Date();
    const timeStr = `${now.getHours().toString().padStart(2, '0')}:${now.getMinutes().toString().padStart(2, '0')}:${now.getSeconds().toString().padStart(2, '0')}`;
    
    // 创建文件列表容器
    const fileList = document.createElement('div');
    fileList.style.cssText = 'margin-top: 10px;';
    
    // 显示图片缩略图
    if (images.length > 0) {
        const imageHeader = document.createElement('div');
        imageHeader.style.cssText = 'font-weight: bold; color: #1890ff; margin-bottom: 8px; font-size: 13px;';
        imageHeader.textContent = `📷 图片 (${images.length}):`;
        fileList.appendChild(imageHeader);
        
        const imageGrid = document.createElement('div');
        imageGrid.style.cssText = 'display: flex; flex-wrap: wrap; gap: 8px; margin-bottom: 10px;';
        
        let loadedCount = 0;
        images.forEach((img, index) => {
            const thumbDiv = document.createElement('div');
            thumbDiv.style.cssText = 'position: relative; width: 70px; height: 70px;';
            thumbDiv.innerHTML = `
                <div style="width: 70px; height: 70px; background: #f0f0f0; border-radius: 4px; border: 1px solid #e8e8e8; display: flex; align-items: center; justify-content: center;">
                    <span style="font-size: 20px; color: #999;">📷</span>
                </div>
                <span style="position: absolute; bottom: 2px; left: 2px; right: 2px; background: rgba(0,0,0,0.6); color: white; font-size: 10px; padding: 2px 4px; border-radius: 2px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;" title="${img.name}">${img.name.length > 10 ? img.name.substring(0, 10) + '...' : img.name}</span>
            `;
            imageGrid.appendChild(thumbDiv);
            
            // 异步加载图片
            const reader = new FileReader();
            reader.onload = function(e) {
                const imgEl = thumbDiv.querySelector('div');
                if (imgEl) {
                    imgEl.style.backgroundImage = `url(${e.target.result})`;
                    imgEl.style.backgroundSize = 'cover';
                    imgEl.style.backgroundPosition = 'center';
                    imgEl.innerHTML = ''; // 移除加载图标
                }
            };
            reader.readAsDataURL(img);
        });
        
        fileList.appendChild(imageGrid);
    }
    
    // 显示压缩包
    if (archives.length > 0) {
        const archiveHeader = document.createElement('div');
        archiveHeader.style.cssText = 'font-weight: bold; color: #52c41a; margin-bottom: 8px; font-size: 13px;';
        archiveHeader.textContent = `📦 压缩包 (${archives.length}):`;
        fileList.appendChild(archiveHeader);
        
        const archiveGrid = document.createElement('div');
        archiveGrid.style.cssText = 'display: flex; flex-wrap: wrap; gap: 8px; margin-bottom: 10px;';
        
        archives.forEach((archive, index) => {
            const archiveDiv = document.createElement('div');
            archiveDiv.style.cssText = 'position: relative; width: 70px; height: 70px;';
            archiveDiv.innerHTML = `
                <div style="width: 70px; height: 70px; background: #f6ffed; border-radius: 4px; border: 1px solid #b7eb8f; display: flex; flex-direction: column; align-items: center; justify-content: center; font-size: 10px; text-align: center; color: #52c41a;">
                    <span style="font-size: 24px; line-height: 1;">📦</span>
                    <span style="font-size: 9px; color: #666; padding: 0 2px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; max-width: 60px;">${archive.name.length > 10 ? archive.name.substring(0, 10) + '...' : archive.name}</span>
                </div>
            `;
            archiveGrid.appendChild(archiveDiv);
        });
        
        fileList.appendChild(archiveGrid);
    }
    
    // 添加时间戳
    const timestamp = document.createElement('div');
    timestamp.style.cssText = 'font-size: 11px; color: #999; margin-top: 5px; text-align: right; border-top: 1px solid #f0f0f0; padding-top: 5px;';
    timestamp.textContent = `上传时间: ${timeStr}`;
    fileList.appendChild(timestamp);
    
    historyContainer.appendChild(fileList);
    
    // 自动滚动到底部
    historyContainer.scrollTop = historyContainer.scrollHeight;
    
    // 10秒后自动隐藏
    setTimeout(() => {
        if (historyContainer && historyContainer.parentNode) {
            historyContainer.style.opacity = '0';
            historyContainer.style.transition = 'opacity 0.5s';
            setTimeout(() => {
                if (historyContainer && historyContainer.parentNode) {
                    historyContainer.remove();
                }
            }, 500);
        }
    }, 10000);
}

// 拖拽上传支持
document.addEventListener('DOMContentLoaded', function() {
    const imageUpload = document.getElementById('imageUpload');
    const archiveUpload = document.getElementById('archiveUpload');
    
    if (imageUpload) {
        ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
            imageUpload.addEventListener(eventName, preventDefaults, false);
        });
        
        function preventDefaults(e) {
            e.preventDefault();
            e.stopPropagation();
        }
        
        imageUpload.addEventListener('drop', function(e) {
            const files = e.dataTransfer.files;
            const imageInput = document.getElementById('imageFiles');
            handleFiles(files, imageInput);
        });
    }
    
    if (archiveUpload) {
        ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
            archiveUpload.addEventListener(eventName, preventDefaults, false);
        });
        
        archiveUpload.addEventListener('drop', function(e) {
            const files = e.dataTransfer.files;
            const archiveInput = document.getElementById('archiveFiles');
            handleFiles(files, archiveInput);
        });
    }
    
    function handleFiles(files, input) {
        const dataTransfer = new DataTransfer();
        for (const file of files) {
            dataTransfer.items.add(file);
        }
        input.files = dataTransfer.files;
        input.dispatchEvent(new Event('change'));
    }
});