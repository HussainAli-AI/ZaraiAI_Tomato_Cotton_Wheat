"""Grad-CAM implementation for Visual Explainability in ZaraiAI."""
import torch
import torch.nn.functional as F
import numpy as np
from PIL import Image
import cv2

class GradCAM:
    """
    Grad-CAM (Gradient-weighted Class Activation Mapping) for CNN feature explainability.
    Visualizes the spatial regions in a leaf image that contributed most to the disease prediction.
    """
    def __init__(self, model, target_layer=None):
        self.model = model
        self.model.eval()
        
        # Auto-detect target layer if not explicitly provided
        if target_layer is None:
            if hasattr(model, "target_layer"):
                self.target_layer = model.target_layer
            elif hasattr(model, "features"):
                self.target_layer = model.features[-1]
            else:
                raise ValueError("Could not automatically locate target convolutional layer for Grad-CAM.")
        else:
            self.target_layer = target_layer
            
        self.gradients = None
        self.activations = None
        
        # Register forward and backward hooks
        self._register_hooks()
        
    def _register_hooks(self):
        def forward_hook(module, input, output):
            self.activations = output
            
        def backward_hook(module, grad_in, grad_out):
            self.gradients = grad_out[0]
            
        self.target_layer.register_forward_hook(forward_hook)
        self.target_layer.register_full_backward_hook(backward_hook)
        
    def generate_heatmap(self, input_tensor, target_class=None):
        """
        Generate raw normalized Grad-CAM heatmap for a single input tensor [1, C, H, W].
        """
        self.model.zero_grad()
        
        # Forward pass
        output = self.model(input_tensor)
        
        if target_class is None:
            target_class = torch.argmax(output, dim=1).item()
            
        # Target score for backprop
        score = output[0, target_class]
        score.backward()
        
        # Pool gradients across spatial dimensions (Global Average Pooling of grads)
        pooled_gradients = torch.mean(self.gradients, dim=[0, 2, 3])
        
        # Weight activations by pooled gradients
        activations = self.activations[0]
        for i in range(activations.shape[0]):
            activations[i, :, :] *= pooled_gradients[i]
            
        # ReLU on weighted sum of activation maps
        heatmap = torch.mean(activations, dim=0).squeeze()
        heatmap = F.relu(heatmap)
        
        # Normalize to [0, 1]
        heatmap_max = torch.max(heatmap)
        if heatmap_max > 0:
            heatmap /= heatmap_max
            
        return heatmap.cpu().detach().numpy()
        
    def overlay_heatmap(self, original_pil_image, heatmap, alpha=0.5, colormap=cv2.COLORMAP_JET):
        """
        Superimpose colored heatmap on top of original PIL image.
        Returns combined PIL image.
        """
        orig_np = np.array(original_pil_image)
        h, w = orig_np.shape[:2]
        
        # Resize heatmap to match image dimensions
        resized_heatmap = cv2.resize(heatmap, (w, h))
        
        # Convert heatmap to RGB colormap
        heatmap_uint8 = np.uint8(255 * resized_heatmap)
        colored_heatmap = cv2.applyColorMap(heatmap_uint8, colormap)
        colored_heatmap = cv2.cvtColor(colored_heatmap, cv2.COLOR_BGR2RGB)
        
        # Blend original with heatmap
        blended = np.uint8(orig_np * (1 - alpha) + colored_heatmap * alpha)
        
        return Image.fromarray(blended)
