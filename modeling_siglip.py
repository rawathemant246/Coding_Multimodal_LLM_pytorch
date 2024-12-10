from typing import Optional, Tuple
import torch
import torch.nn as nn



class SiglipVisionConfig:
    
    def __init__(
        
        self,
        hidden_size =768,
        intermediate_size = 3072,
        num_hidden_layer = 12,
        num_attention_heads=12,
        num_channel=3,
        image_size=224,
        patch_size=16,
        layer_norm_eps=1e-6,
        attention_dropout=0.0,
        num_image_tokens : int = None,
        **kwargs
    ):
        
        super().__init__()
        
        self.hidden_size = hidden_size
        self.intermediate_size = intermediate_size
        self.num_hidden_layers = num_hidden_layer
        self.num_attention_heads = num_attention_heads
        self.num_channels = num_channel
        self.patch_size = patch_size
        self.image_size = image_size
        self.attention_dropout = attention_dropout
        self.layer_norm_eps = layer_norm_eps
        self.num_image_tokens = num_image_tokens
        

class SiglipVisionEmbeddings(nn.Module):
    
    def __init__(self, config : SiglipVisionConfig):
        super().__init__()
        
        self.config = config
        self.embed_dim = config.hidden_size
        self.image_size = config.image_size
        self.patch_size = config.patch_size
        
        
        self.patch_embedding = nn.Conv2d(
            in_channels=config.num_channels,
            out_channels=self.embed_dim,
            kernel_size=self.patch_size,
            stride=self.patch_size,
            padding = "valid", # It means no padding are added
        )


        self.num_patches = (self.image_size // self.patch_size) **2
        self.num_positions =self.num_patches
        self.position_embedding = nn.Embedding(
            self.num_positions, self.embed_dim)
        self.register_buffer(
            "position_ids",
            torch.arange(self.num_positions).expand((1,-1)),
            persistent=False,
        )
        
    def forward(self, pixel_values: torch.FloatTensor) -> torch.Tensor:
        _,_,height, width = pixel_values.shape #[Batch_size, Channels, Height, Width]
        #convolve the 'patch_size kernel over the image, with no overlapping patches since the stride is equal to the kernel size
        #The output of the convulution will have thshape [Batch_size, Embed_dime, Num_Patches_H, Num_Patches_W]
        #where Num_Patches_H =  height //patche_size and Num_Patches_W = width// patch_size
        
        patch_embeds = self.patch_embedding(pixel_values)
        # [ Batch_size, Embed_Dim, Num_Patches_H, Num_Patches_W] -> [Batche_Size, Embed_Dim, Num_Patches]
        # where Num_Patches = Num_Patches_H * Num_Patches_W
        embeddings = patch_embeds.flatten(2)
        # [Batch_Size , Embed_Dim, Num_Patches] -> [Batch_size, Num_Pathes, Embed_Dim]
        embeddings = embeddings.transpose(1,2)
        #Add position  embeddings to each patch. Each positional encoding is a vector of size (Embed_Dim)
        embeddings = embeddings + self.position_embedding(self.position_ids)
        # [Batch_size, Num_Patches, Embed_Dim]
        return embeddings

# class SiglipAttention(nn.Module):
    
#     def __init__(self, config : SiglipVisionConfig):
        


class SiglipMLP(nn.Module):
    
    def __init__(self, config):
        
        super().__init__()
        
        self.config = config
        self.fc1 = nn.Linear(config.hidden_size, config.intermediate_size)
        self.fc2 = nn.Linear(config.intermediate_size, config.hidden_size)
    
    def forward(self, hidden_size : torch.Tensor) -> torch.Tensor:
        #[Batch_size, Num_Patches, Embded_dim] -> [Batch_size, Num_Patches, Intermediate_Size]
        hidden_states = self.fc1(hidden_states)
        #hidden_states : [Batch_sizez, Num_Patches, Intermediate_Size]
        hidden_states = nn.functional.gelu(hidden_states, approximate="tanh")
        #[Batch_size, Num_patches, Intermediate_size] -> [Batch_size, Num+Patches, Embed_Dim]
        hidden_states = self.fc2(hidden_states)
        
        return hidden_states
    


class SiglipEncoderLayer(nn.Module):
    
    pass 



class SiglipEncoder(nn.Module):
    
    def __init__(self, config : SiglipVisionConfig):
        
        super().__init__()
        self.config = config
        self.layers = nn.ModuleList(
            [SiglipEncoderLayer(config) for _ in range(config.num_hidden_layers)]
            
        )
    
    #ignore copy
    
    def forward(self, input_embeds : torch.Tensor)  -> torch.Tensor:
        
        #inputs_embed : [Batch_size, Num_Patches, Embed_Dime]
        
        hidden_states = input_embeds
        
        for encoder_layer in self.layers:
            
            # [ Batch_Size, Num_Patches, Embed_Dim] -> [Batch_Size, Num_Patches, Embed_Dim]
            
            hidden_states = encoder_layer(hidden_states)
            
        
        return hidden_states
    
        
                

class SiglipVisionTransformer(nn.Module):
    
    def __init__(self, config : SiglipVisionConfig):
        
        super().__init__()
        
        self.config = config
        embed_dim = config.hidden_size
        self.embeddings = SiglipVisionEmbeddings(config)
        self.encoder = SiglipEncoder(config)
        self.post_layernorm = nn.LayerNorm(embed_dim, eps=config.layer_norm_eps)
    
    def forward(self, pixel_value:torch.Tensor) -> torch.Tensor:
        #pixel_value : [Batch_size, channels, Height, Width] -> [Btch_size, Num_Patches, Embed_dim]
        
        hidden_states = self.embeddings(pixel_value)
        
        last_hidden_state = self.encoder(inputs_embeds=hidden_states)
        
        last_hidden_state = self.post_layernorm(last_hidden_state)
        
        return last_hidden_state




class SiglipVisionModel(nn.Module):
    
    def __init__(self, config: SiglipVisionConfig):
        super().__init__()
        
        self.config = config
        self.vision_model = SiglipVisionTransformer(config)
        
    
    def forward(self, pixel_values) -> Tuple:
        # [Batch_size, channels, Height, Width] -> [Batch_size, Num_Patches, Embed_Dim]
        return self.vision_model(pixel_values=pixel_values  )
        