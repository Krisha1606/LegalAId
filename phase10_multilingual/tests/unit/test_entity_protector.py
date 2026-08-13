import pytest
from src.services.entity_protector import EntityProtector

def test_protect_amounts():
    protector = EntityProtector()
    text = "The amount is ₹30,000 for the damages."
    protected, mapping = protector.protect(text)
    
    assert "₹30,000" not in protected
    assert "__PROTECTED_ENTITY_0__" in protected
    
    restored = protector.restore(protected, mapping)
    assert restored == text

def test_protect_acts_and_sections():
    protector = EntityProtector()
    text = "Under Consumer Protection Act, 2019 Section 35 applies."
    protected, mapping = protector.protect(text)
    
    assert "Consumer Protection Act, 2019" not in protected
    assert "Section 35" not in protected
    assert len(mapping) == 2
    
    restored = protector.restore(protected, mapping)
    assert restored == text

def test_protect_multiple_same_entities():
    protector = EntityProtector()
    text = "Amount ₹30,000. Another ₹30,000."
    protected, mapping = protector.protect(text)
    
    assert "₹30,000" not in protected
    # It should only map ₹30,000 once
    assert len(mapping) == 1 
    assert protected == "Amount __PROTECTED_ENTITY_0__. Another __PROTECTED_ENTITY_0__."
    
    restored = protector.restore(protected, mapping)
    assert restored == text
