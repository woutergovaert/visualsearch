import { propTypes } from 'formsy-react'
import React from 'react'
import Form, {
  Input,
  MultiSelect,
  SubmitButton,
} from 'react-form-component'

const BasicExampleForm = (props) =>
  <Form fields={['url', 'methods']} mandatory={['url']} className="w-1/2 ">
    <Input
    debounceTime={500}
    type="text"
    label="Image URL"
    name="url"
  />
    <MultiSelect
    className=""
    
    label="Choose Methods"
    name="methods"
    options={[
      'ImageTagging',
      'OCR',
      'ImageDescription',
      'Custom',
      'ObjectDetection'
    ]}
    placeholder="All"
    prefix=""
    suffix=""
  />
    <SubmitButton
      onClick={fields => props.submit(fields)}
    >Submit</SubmitButton>
  </Form>

export default BasicExampleForm