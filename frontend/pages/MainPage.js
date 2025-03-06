const MainPage = {
    template: `<div>
<div class="container mt-4 mb-4">
  <div class="card">
    <div class="card-body">

        <div class="text-center mb-4">
          <h1><u>Submit Your Query</u></h1>
        </div>

        <div class="d-flex justify-content-center align-items-center">
          <div class="me-3">
            <input type="text" v-model="textInput" placeholder="Type Text" class="form-control">
          </div>
          <div>
            <input type="file" @change="handleFileUpload" class="form-control">
          </div>
        </div>

        <div class="text-center mt-3">
          <button @click="messageSender" class="btn btn-outline-success mb-3">Send</button>
        </div>

    </div>
  </div>
</div>
</div>
    `,
    
    data() {
      return {
        textInput: '',
        file: null,
      };
    },
  
    methods: {
      handleFileUpload(event) {
        this.file = event.target.files[0];
      },

      async messageSender() {
        const formData = new FormData();
        formData.append('text-input', this.textInput);
        if (this.file) {
          formData.append('file-upload', this.file);
        }

        const res = await fetch(location.origin + '/api/submit', {
          method: 'GET',
          body: formData
        });

        if (res.ok) {
          console.log("Form submitted successfully!");
          // Handle successful submission
        } else {
          alert("There was an error submitting the form.");
          // Handle error
        }
      }
    }
  };
  
  export default MainPage;